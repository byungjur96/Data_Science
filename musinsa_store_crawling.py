from bs4 import BeautifulSoup, Tag
import urllib.request
import ssl  # urllib의 오류 해결을 위한 라이브러리
import time
# urlopen error [SSL: CERTIFICATE_VERIFY_FAILED] certificate verify failed (_ssl.c:749)


root_url = 'https://store.musinsa.com'
context = ssl._create_unverified_context()


def get_submenu_link(menu):
    for sub_menu in category_link[menu]:
        sub_num = category_link[menu][sub_menu]

        # 각 하위메뉴의 전체 페이지 수를 먼저 파악
        sub_link = 'https://store.musinsa.com/app/items/lists/{0}'.format(sub_num)
        with urllib.request.urlopen(sub_link, context=context) as sub_menu_url:
            sub_menu_page = sub_menu_url.read()
        sub_menu_data = BeautifulSoup(sub_menu_page, 'lxml')
        pages = int(sub_menu_data.find('span', {'class': 'totalPagingNum'}).get_text().strip())
        print(sub_menu + ' has total ' + str(pages) + ' pages.')

        # 각 페이지마다의 주소
        for page in range(pages):
            page_num = page + 1
            sub_link = '{0}/app/items/lists/{1}/?category=&d_cat_cd={1}&u_cat_cd=&' \
                       'brand=&sort=pop&display_cnt=120&page={2}&page_kind=category&list_kind=small&' \
                       'free_dlv=&ex_soldout=&sale_goods=&exclusive_yn=&price=&color=&a_cat_cd=&sex=&size=&tag=&' \
                       'popup=&brand_favorite_yn=&goods_favorite_yn=&blf_yn=&=&price1=&price2=&brand_favorite=&' \
                       'goods_favorite=&chk_exclusive=&chk_sale=&chk_soldout='.format(root_url,sub_num, page_num)
            print('Page ' + str(page_num) + ' Starts.')
            get_product_list(sub_link)


def get_product_list(page_link):
    with urllib.request.urlopen(page_link, context=context) as page_url:
        page_info = page_url.read()
    sample_data = BeautifulSoup(page_info, 'lxml')

    item_boxs = sample_data.find('ul', {'id': 'searchList'})
    item_box = item_boxs.find_all('li', {'class': 'li_box'})
    for item in item_box:
        item_info = item.find('div', {'class': 'li_inner'}).find('a')['href']
        print('About ' + item_info)
        get_product_info(root_url+item_info)


# 하나의 제품에 대해서 상세 정보를 받아오는 함수
def get_product_info(sub_url):
    print(sub_url)
    with urllib.request.urlopen(sub_url, context=context) as specific_url:
        specific_page = specific_url.read()

    # 페이지 파싱
    specific_data = BeautifulSoup(specific_page, 'lxml')
    # 이름
    product_name = specific_data.find('span', {'class': 'product_title'}).find('span')
    print('이름: ' + product_name.get_text())
    category_arr = []
    product_categories = specific_data.find('p', {'class': 'item_categories'}).children
    for product_category in product_categories:
        if isinstance(product_category, Tag):
            category_arr.append(product_category)

    # 브랜드
    product_brand = category_arr[0].get_text()
    print('브랜드: ' + product_brand)

    # 종류
    product_type = category_arr[1].get_text()
    print('종류: ' + product_type)

    # 세부 종류
    product_subtype = category_arr[2].get_text()
    print('세부 종류: ' + product_subtype)

    # 제품 정리 목록을 받아온다.
    product_info_arr = []

    # product_Article Class 는 Product Info, Delivery Info, Price Info 3개로 나뉘어져 있음 -> 맨 앞의 1개만 받아오기
    product_info = specific_data.find('ul', {'class': 'product_article'}).children
    for info in product_info:
        if isinstance(info, Tag):
            product_info_arr.append(info)

    # 시즌
    if product_info_arr is None:
        print('No Information!')
        time.sleep(3)

    else:
        product_season = product_info_arr[1].find('strong').get_text().replace('\t', '').replace(' ', '').strip()
        print('시즌: ' + product_season)

        # 성별
        product_gender = product_info_arr[1].find('span', {'class': 'txt_gender'}).get_text().strip()
        print('성별: ' + product_gender)
        product_popularity_arr = []
        product_popularity = product_info_arr[2].find('p', {'class': 'product_article_contents'}).find_all('strong')
        for popularity in product_popularity:
            if isinstance(popularity, Tag):
                product_popularity_arr.append(popularity)

        # 조회수
        product_view = product_popularity_arr[0].get_text()
        print('조회수: ' + product_view)

        # 장바구니+관심
        product_interest = product_popularity_arr[1].get_text()
        print('장바구니+관심상품: ' + product_interest)

        # 누적 판매
        product_total_sell = product_info_arr[3].find('p', {'class': 'product_article_contents'}).find('strong').get_text()
        print('누적 판매: ' + product_total_sell)

        # 좋아요
        product_like = product_info_arr[4].find('span', {'class': 'prd_like_cnt'}).get_text()
        print('좋아요: ' + product_like)

        # 해시태그
        product_hashtag_arr = []
        product_hashtag = product_info_arr[6].find_all('a', {'class': 'listItem'})
        for hashtag in product_hashtag:
            if isinstance(hashtag, Tag):
                product_hashtag_arr.append(hashtag['onclick'].split("'")[1])
        print(product_hashtag_arr)

        # 가격
        product_price = int(specific_data.find('span', {'id': 'goods_price'}).get_text().replace(',', ''))
        print('가격: ' + str(product_price))


# 메인 화면을 파싱한다.
with urllib.request.urlopen(root_url, context=context) as url:
    home = url.read()
home_data = BeautifulSoup(home, 'lxml')

# 홈페이지 내의 카테고리를 딕셔너리 타입으로 만든다.
category_link = dict()
category_group = home_data.find('nav', {'class': 'nav_menu'})
categories = category_group.find_all('div', {'class': 'nav_category'})

# 딕셔너리 타입으로 만든다.
for category in categories:
    name = category.find('span', {'class': 'nav_kr'}).get_text().split(' (')[0]
    category_link[name] = dict()
    sub_category_groups = category.find('ul', {'class': 'nav_category_menu'})
    sub_category = []

    for sub_category_group in sub_category_groups:

        # NavigableString 객체를 걸러내준다.
        if isinstance(sub_category_group, Tag):
            temp = sub_category_group.find('a')
            category_link[name][temp.get_text().strip().split(' (')[0]] = temp['href'].split('/')[-1]

for category in category_link:
    print('Start ' + category + ' Category.')
    get_submenu_link(category)
