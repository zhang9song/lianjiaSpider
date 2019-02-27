import json
import re
import time

import requests
from bs4 import BeautifulSoup

headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 6.1) AppleWebKit/537.11 (KHTML, like Gecko) Chrome/23.0.1271.64 Safari/537.11',
    'Accept': 'text/html;q=0.9,*/*;q=0.8',
    'Accept-Charset': 'ISO-8859-1,utf-8;q=0.7,*;q=0.3',
    'Accept-Encoding': 'gzip',
    'Connection': 'close',
    'Referer': 'http://www.baidu.com/link?url=_andhfsjjjKRgEWkj7i9cFmYYGsisrnm2A-TN3XZDQXxvGsM9k9ZZSnikW2Yds4s&amp;amp;wd=&amp;amp;eqid=c3435a7d00006bd600000003582bfd1f'
}
XQURL = 'https://bj.lianjia.com/xiaoqu'
ESF_URL = 'https://bj.lianjia.com/ershoufang'
CJ_URL = 'https://bj.lianjia.com/chengjiao'
districts = ['dongcheng', 'xicheng', 'haidian', 'chaoyang', 'fengtai', 'shijingshan', 'mentougou', 'daxing',
             'shunyi', 'huairou', 'yanqing', 'miyun', 'pinggu', 'tongzhou']
XQ_CSV_PATH = './datasets/xiaoqu.csv'
CJ_CSV_PATH = './datasets/cj.csv'
ESF_CSV_PATH = './datasets/esf.csv'

#获取该行政区内得小区和总页数
def get_dist_xiaoqu_pg_num():
    d_x_pg_num = {}
    for d in districts:
        d_url = '{0}/{1}/'.format(XQURL, d)
        r = requests.get(d_url, headers=headers)
        html = r.content
        soup = BeautifulSoup(html, 'html.parser')
        total_pg = soup.find_all('div', class_='house-lst-page-box')
        tp_num = json.loads(total_pg[0]['page-data'])['totalPage']
        d_x_pg_num[d] = tp_num
        time.sleep(1)
    return d_x_pg_num

#获取小区得经纬度
def get_xiaoqu_latitude(url):
    r = requests.get(url, headers=headers)
    html = r.content
    soup = BeautifulSoup(html, 'html.parser')
    items = soup.find_all('script')
    time.sleep(0.5)
    regex = '''resblockPosition(.+)'''
    items = re.search(regex, items[15].text)
    content = items.group()[:-1]
    longitude_latitude = content.split(':')[1]
    return longitude_latitude[1:-1]

#按照小区椰树获取小区信息，包括名称，修建日期，经纬度，平均价格
def get_xiaoqu_items(xiaoqu_page):
    for key in xiaoqu_page.keys():
        for i in range(1, xiaoqu_page[key] + 1):
            url = '{0}/{1}/pg{2}/'.format(XQURL, key, i)
            r = requests.get(url, headers=headers)
            html = r.content
            try:
                soup = BeautifulSoup(html, 'html.parser')
                items = soup.find_all('li', class_='xiaoquListItem')
                for item in items:
                    item_content = []
                    item_content.append(item['data-id'])
                    title_el = item.find('div', class_='title')
                    item_content.append(title_el.a.text)
                    item_year = item.find('div', class_='positionInfo').text
                    years = re.findall('\d+', item_year)
                    item_content.append(years[0])
                    lat_url = '{0}/{1}/'.format(XQURL, item['data-id'])
                    lat = get_xiaoqu_latitude(lat_url)
                    item_content.append(lat)
                    item_content.append(key)
                    item_content.append(item.find('div', class_='totalPrice').span.text)
                    with open(XQ_CSV_PATH, 'a+') as xiaoqu_csv_file:
                        xiaoqu_csv_file.write(','.join(item_content) + '\n')
            except Exception as e:
                print(e)
                continue
            print(key, 'page', i, 'done.')
            time.sleep(0.5)
    xiaoqu_csv_file.close()

#从已有小区文件中获取小区信息
def get_xiaoqu_ids():
    id_lst = []
    with open(XQ_CSV_PATH, 'r') as xiaoqu_csv_file:
        lines = xiaoqu_csv_file.readlines()
        for line in lines[1:]:
            line_sp = line.split(',')
            id_lst.append(line_sp)
    return id_lst

#获取二手房详细信息
def get_esf_detial_info(items, id):
    for item in items:
        try:
            hinfo = item.find('div', class_='houseInfo')
            area = re.findall('\d+\.\d+', hinfo.text)[0]
            total_price = item.find('div', class_='totalPrice').span.text
            unitPrice = item.find('div', class_='unitPrice')['data-price']
            with open(ESF_CSV_PATH, 'a+') as ershoufang_csv_file:
                ershoufang_csv_file.write(
                    ','.join([id[1], id[2], id[3], id[4], id[5], area, total_price, unitPrice]) + '\n')
        except Exception as e:
            print(e)
            continue

#获取成交房信息
def get_cjf_detial_info(items, ids):
    for item in items:
        try:
            title = item.find('div', class_='title').a.text
            area = re.findall('\d+\.\d+', title)[0]
            dealDate = item.find('div', class_='dealDate').text
            total_price = item.find('div', class_='totalPrice').span.text
            unitPrice = item.find('div', class_='unitPrice').span.text
            dealCycle = item.find('span', class_='dealCycleTxt')
            deal_spans = dealCycle.find_all('span')
            quote_price = re.findall('\d+', deal_spans[0].text)[0]
            deal_days = re.findall('\d+', deal_spans[1].text)[0]
            with open(CJ_CSV_PATH, 'a+') as cjfang_csv_file:
                cjfang_csv_file.write(
                    ','.join([ids[1], ids[2], ids[3], ids[4], ids[5], area, dealDate, total_price, unitPrice,
                              quote_price, deal_days, (str(float(quote_price) - float(total_price)) + '\n')]))
        except Exception as e:
            print(e)
            continue


def get_ershoufang_items(xids):
    for id in xids:
        url = '{0}/c{1}/'.format(ESF_URL, id[0])
        r = requests.get(url, headers=headers)
        html = r.content
        soup = BeautifulSoup(html, 'html.parser')
        items = soup.find_all('li', class_='LOGCLICKDATA')
        get_esf_detial_info(items, id)
        pages = soup.find_all('div', class_='house-lst-page-box')
        if pages:
            tp_num = json.loads(pages[0]['page-data'])['totalPage']
            for i in range(2, tp_num + 1):
                url = '{0}/pg{1}c{2}/'.format(ESF_URL, i, id[0])
                r = requests.get(url, headers=headers)
                html = r.content
                soup = BeautifulSoup(html, 'html.parser')
                items = soup.find_all('li', class_='LOGCLICKDATA')
                get_esf_detial_info(items, id)
                print(id, 'page', i, 'done')
                time.sleep(0.5)
        print(id, 'done')
        time.sleep(0.5)


def get_chengjiao_items(xids):
    for id in xids:
        url = '{0}/c{1}/'.format(CJ_URL, id[0])
        r = requests.get(url, headers=headers)
        html = r.content
        soup = BeautifulSoup(html, 'html.parser')
        items = soup.find('ul', class_='listContent')
        get_cjf_detial_info(items.find_all('li'), id)
        pages = soup.find_all('div', class_='house-lst-page-box')
        if pages:
            tp_num = json.loads(pages[0]['page-data'])['totalPage']
            for i in range(2, tp_num + 1):
                url = '{0}/pg{1}c{2}/'.format(CJ_URL, i, id[0])
                r = requests.get(url, headers=headers)
                html = r.content
                soup = BeautifulSoup(html, 'html.parser')
                items = soup.find('ul', class_='listContent')
                get_cjf_detial_info(items.find_all('li'), id)
                print(id, 'CHENGJIAO', 'page', i, 'done')
                time.sleep(0.5)
        print(id, 'CHENGJIAO', 'done')
        time.sleep(0.5)


if __name__ == '__main__':
    # dxpgn = {'dongcheng': 30, 'xicheng': 30, 'haidian': 30, 'chaoyang': 30, 'fengtai': 30, 'shijingshan': 9,
    #          'mentougou': 8, 'daxing': 17, 'shunyi': 11, 'huairou': 3, 'yanqing': 2, 'miyun': 4, 'pinggu': 2,
    #          'tongzhou': 22}

    xiaoqu_lst = get_xiaoqu_ids()
    get_chengjiao_items(xiaoqu_lst)
    get_ershoufang_items(xiaoqu_lst)
