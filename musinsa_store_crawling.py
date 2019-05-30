from bs4 import BeautifulSoup, Tag
import urllib.request
import ssl  # urllib의 오류 해결을 위한 라이브러리
import time
import datetime
import json
from collections import OrderedDict
# urlopen error [SSL: CERTIFICATE_VERIFY_FAILED] certificate verify failed (_ssl.c:749)

root_url = 'https://store.musinsa.com'
context = ssl._create_unverified_context()
total = 0
top = 0
bottom = 0
category_code = {
    'top': '001',
    'bottom': '003'
}


def get_submenu_link(menu):
    # 메뉴의 코드 파악
    code = category_code[menu]
    sub_link = 'https://store.musinsa.com/app/items/lists/{0}'.format(code)
    with urllib.request.urlopen(sub_link, context=context) as sub_menu_url:
        sub_menu_page = sub_menu_url.read()
    sub_menu_data = BeautifulSoup(sub_menu_page, 'lxml')
    pages = int(sub_menu_data.find('span', {'class': 'totalPagingNum'}).get_text().strip())
    print(menu + ' has total ' + str(pages) + ' pages.')

    # 각 페이지마다의 주소
    for page in range(pages):
        page_num = page + 1
        sub_link = '{0}/app/items/lists/{1}/?category=&d_cat_cd={1}&u_cat_cd=&' \
                   'brand=&sort=pop&display_cnt=120&page={2}&page_kind=category&list_kind=small&' \
                   'free_dlv=&ex_soldout=&sale_goods=&exclusive_yn=&price=&color=&a_cat_cd=&sex=&size=&tag=&' \
                   'popup=&brand_favorite_yn=&goods_favorite_yn=&blf_yn=&=&price1=&price2=&brand_favorite=&' \
                   'goods_favorite=&chk_exclusive=&chk_sale=&chk_soldout='.format(root_url, code, page_num)
        print('Page ' + str(page_num) + ' Starts.')
        get_product_list(sub_link)


# 하나의 페이지에 있는 모든 product 들의 링크를 받아온다.
def get_product_list(page_link):
    global top, bottom
    with urllib.request.urlopen(page_link, context=context) as page_url:
        page_info = page_url.read()
    sample_data = BeautifulSoup(page_info, 'lxml')

    item_boxes = sample_data.find('ul', {'id': 'searchList'})
    item_box = item_boxes.find_all('li', {'class': 'li_box'})
    for item in item_box:
        item_info = item.find('div', {'class': 'li_inner'}).find('a')['href']
        p_name, p_characteristic = get_product_info(root_url+item_info)
        if p_characteristic['category'] == '상의':
            category_json[category]['top'+str(top)] = p_characteristic
            top += 1
        else:
            category_json['category']['bottom' + str(bottom)] = p_characteristic
            bottom += 1


# 하나의 제품에 대해서 상세 정보를 받아온다.
def get_product_info(sub_url):
    global total
    total += 1

    print(sub_url)

    product_dict = OrderedDict()
    with urllib.request.urlopen(sub_url, context=context) as specific_url:
        specific_page = specific_url.read()

    # 페이지 파싱
    specific_data = BeautifulSoup(specific_page, 'lxml')
    # 이름
    product_name = specific_data.find('span', {'class': 'product_title'}).find('span').get_text()

    category_arr = []
    product_categories = specific_data.find('p', {'class': 'item_categories'}).children
    for product_category in product_categories:
        if isinstance(product_category, Tag):
            category_arr.append(product_category)

    # 브랜드
    if len(category_arr) > 0:
        product_brand = category_arr[0]
        if product_brand is not None:
            product_dict["brand"] = product_brand.get_text()
    else:
        print('No Brand.')

    # 종류
    if len(category_arr) > 1:
        product_type = category_arr[1]
        if product_type is not None:
            product_dict["category"] = product_type.get_text()
    else:
        print('No Type.')

    # 세부 종류
    if len(category_arr) > 2:
        product_subtype = category_arr[2]
        if product_subtype is not None:
            product_dict["subCategory"] = product_subtype.get_text()
    else:
        print('No Subtype.')

    # 시즌
    product_season = specific_data.find('span', {'class': 'txt_gender'}).parent.find('strong')
    if product_season:
        product_season = product_season.get_text().replace('\t', '').replace(' ', '').strip()
        product_dict["season"] = product_season
    else:
        print('No Season.')

    # 성별
    product_gender = specific_data.find('span', {'class': 'txt_gender'})
    if product_gender is not None:
        product_dict["gender"] = product_gender.get_text().strip()
    else:
        print('No Gender.')

    # 조회수
    product_view = specific_data.find_all('span', {'class': 'pageview_number'})[0].previous_sibling
    if product_view is not None:
        product_dict["totalView"] = int(product_view.get_text().replace(',', ''))
    else:
        print('No Total View.')

    # 장바구니+관심
    product_interest = specific_data.find('span', {'class': 'wish_number'})
    if product_interest is not None:
        product_dict["wishNum"] = int(product_interest.previous_sibling.get_text().replace(',', ''))
    else:
        print('No Interest.')

    # 누적 판매
    if len(specific_data.find_all('span', {'class': 'pageview_number'})) > 1:
        product_total_sell = int(specific_data.find_all('span', {'class': 'pageview_number'})[1].previous_sibling.get_text().replace(',', '').replace('개', ''))
    else:
        product_total_sell = 0
    product_dict["totalSell"] = product_total_sell

    # 좋아요
    product_like = specific_data.find('span', {'class': 'prd_like_cnt'})
    if product_like:
        product_like = product_like.get_text()
    else:
        product_like = 0
    product_dict["totalLike"] = product_like

    # 해시태그
    product_hashtag_arr = []
    product_hashtag = specific_data.find_all('a', {'class': 'listItem'})
    for hashtag in product_hashtag:
        if isinstance(hashtag, Tag):
            product_hashtag_arr.append(hashtag['onclick'].split("'")[1])
    product_dict["hashTag"] = product_hashtag_arr

    # 가격
    product_price = specific_data.find('span', {'id': 'goods_price'})
    if product_price is not None:
        product_dict["price"] = int(product_price.get_text().replace(',', ''))
    return [product_name, product_dict]


# 메인 화면을 파싱한다.
start_time = time.time()
print('Start at ' + str(datetime.datetime.now()))

with urllib.request.urlopen(root_url, context=context) as url:
    home = url.read()
home_data = BeautifulSoup(home, 'lxml')

# 홈페이지 내의 카테고리를 딕셔너리 타입으로 만든다.
category_json = OrderedDict()
category_group = home_data.find('nav', {'class': 'nav_menu'})
categories = category_group.find_all('div', {'class': 'nav_category'})

# 딕셔너리 타입으로 만든다.
for category in categories:
    name = category.find('span', {'class': 'nav_kr'}).get_text().split(' (')[0]
    sub_category_groups = category.find('ul', {'class': 'nav_category_menu'})
    sub_category = []

for category in category_code:
    print('<' + category + '>')
    category_json[category] = OrderedDict()
    get_submenu_link(category)
    with open(category+'.json', 'w', encoding='utf-8') as make_file:
        json.dump(category_json[category], make_file, ensure_ascii=False, indent="\t")
    now = time.time()
    print('Total ' + str(total) + ' Products.')
    print('Takes ' + str(start_time-now) + ' sec')
    start_time = now


print('Ends at ' + str(datetime.datetime.now()))

