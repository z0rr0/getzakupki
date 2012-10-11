#!/usr/bin/env python3
#-*- coding: utf-8 -*-

import sys, json, re, time, datetime
from urllib import parse
from winners import *

DEBUG = True
CONFIG = "config.conf"

# orderName - название заказа
# _orderNameMorphology - с учетом всех форм слов
# _orderNameStrict - строгое соответствие
# placingWayType - способ размещения заказа
# _placementStages - подача заявок
#     работа комиссии
#     размещение завершено
#     размещение отменено
# initiatorFullName - заказчик
# initiatorId - hidden
# priceRange - начальная цена
# currencyCode - валюта
# _smallBisnes - для субъектов малого предпринимательства

def debug_print(er):
    global DEBUG
    if DEBUG: print(er)

def main():
    global DEBUG, CONFIG
    config = get_config_data(CONFIG)
    url_example = "http://zakupki.gov.ru/pgz/public/action/search/simple/result?"
    url_info = "http://zakupki.gov.ru/pgz/printForm?type=NOTIFICATION&id="
    url_fullinfo = "http://zakupki.gov.ru/pgz/public/action/orders/info/common_info/show?notificationId="
    url_date = "http://zakupki.gov.ru/pgz/public/action/orders/info/commission_work_result/show?notificationId="
    params = {'orderName': '', '_orderNameMorphology': 'on', '_orderNameStrict': 'on', 'placingWayType': 'EF', 
        '_placementStages': 'on', '_placementStages': 'on', 
        'placementStages': 'FO', '_placementStages': 'on', '_placementStages': 'on',
        'initiatorFullName': '', 'initiatorId': '', 'priceRange': 'H', 'currencyCode': 'RUB', '_smallBisnes': 'on',
        'index': 1, 'sortField': 'lastEventDate', 'descending': 'true', 'tabName': 'FO', 'lotView': 'false', 
        'pageX': '', 'pageY': ''}
    prepate_url = parse.urlencode(params, encoding="utf-8")
    debug_print('create url:' + url_example + prepate_url)
    # regex
    regexps = {'regex_all': re.compile(r"Размещение\s+завершено.*?\((\d+)\)",re.IGNORECASE|re.UNICODE|re.DOTALL),
        'regex_id': re.compile(r'Открытый аукцион в электронной форме.*?showNotificationPrintForm.*?(\d+)\)',re.IGNORECASE|re.UNICODE|re.DOTALL),
        'max_sum': re.compile(r"<maxPriceXml>(.{1,50})</maxPriceXml>",re.IGNORECASE|re.UNICODE|re.DOTALL),
        'garant': re.compile(r"<guaranteeApp>.*?<amount>(.{1,50})</amount>.*?</guaranteeApp>",re.IGNORECASE|re.UNICODE|re.DOTALL),
        'date': re.compile(r"Протокол подведения итогов аукциона.*?от.*?(\d{2}.\d{2}.\d{4})</a>",re.IGNORECASE|re.UNICODE|re.DOTALL)
        # 'max_sum': re.compile(r"<td.*?>.*?Начальная \(максимальная\) цена контракта.*?</td>.*?<td.*?>(.{1,50})Российский рубль",re.IGNORECASE|re.UNICODE|re.DOTALL)
    }
    # regex_all = re.compile(r"Размещение\s+завершено.*?\((\d+)\)",re.IGNORECASE|re.UNICODE|re.DOTALL)
    # regex_id = re.compile(r'Открытый аукцион в электронной форме.*?showNotificationPrintForm.*?(\d+)\)',re.IGNORECASE|re.UNICODE|re.DOTALL)
    today = datetime.date.today()
    todaystr = today.strftime("%d.%m.%Y")
    todaystr = '10.10.2012'
    try:
        i, j, page = 1, 1, 1
        time_start = time.time()
        while i <= j:
            params['index'] = page
            print("page=", page)
            from_url = getURL(url_example + prepate_url)
            if from_url:
                if j == 1:
                    r = regexps['regex_all'].search(from_url)
                    allrecord = r.groups()
                    if len(allrecord):
                        debug_print('all record=' + allrecord[0])     
                        j = int(allrecord[0]) if not config else config['maxitems']
                ids = regexps['regex_id'].findall(from_url)
                i += len(ids)
                # link_in_page = [int(tl) for tl in ids]
                for lp in ids:
                    datek = order_info(regexps['date'], url_date + lp)
                    if datek != todaystr:
                        continue


                    # max_sum = order_info(regexps['max_sum'], url_info + lp)
                    # garant = order_info(regexps['garant'], url_info + lp)
                    # print(lp, max_sum, garant, url_fullinfo + lp)
                # print(link_in_page)
            else:
                i += 1
                print("Error getURL")
            page += 1
        print("delta time = ", time.time() - time_start)
    except (ValueError, IndexError) as e:
        print("Error: {0}".format(e))

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print('Press Ctrl+C, Bye')