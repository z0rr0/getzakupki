#!/usr/bin/env python3
#-*- coding: utf-8 -*-

import sys, json, re, time, datetime, threading
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
    regex_param = re.IGNORECASE|re.UNICODE|re.DOTALL
    urls = {"base": "http://zakupki.gov.ru/pgz/public/action/search/simple/result?",
        "xml": "http://zakupki.gov.ru/pgz/printForm?type=NOTIFICATION&id=",
        "common": "http://zakupki.gov.ru/pgz/public/action/orders/info/common_info/show?notificationId=",
        "protocol": "http://zakupki.gov.ru/pgz/public/action/orders/info/commission_work_result/show?notificationId=",
    }
    regexps = {'regex_all': re.compile(r"Размещение\s+завершено.*?\((\d+)\)",regex_param),
        'regex_id': re.compile(r'Открытый аукцион в электронной форме.*?showNotificationPrintForm.*?(\d+)\)',regex_param),
        'max_sum': re.compile(r"<maxPriceXml>(.{1,50})</maxPriceXml>",regex_param),
        'garant': re.compile(r"<guaranteeApp>.*?<amount>(.{1,50})</amount>.*?</guaranteeApp>",regex_param),
        'date': re.compile(r"Протокол подведения итогов аукциона.*?от.*?(\d{2}.\d{2}.\d{4})</a>",regex_param)
    }
    params = {'orderName': '', '_orderNameMorphology': 'on', '_orderNameStrict': 'on', 'placingWayType': 'EF', 
        '_placementStages': 'on', '_placementStages': 'on', 
        'placementStages': 'FO', '_placementStages': 'on', '_placementStages': 'on',
        'initiatorFullName': '', 'initiatorId': '', 'priceRange': 'H', 'currencyCode': 'RUB', '_smallBisnes': 'on',
        'index': 1, 'sortField': 'lastEventDate', 'descending': 'true', 'tabName': 'FO', 'lotView': 'false', 
        'pageX': '', 'pageY': ''}
    # NOTE: encoding - optional for this case
    prepate_url = parse.urlencode(params, encoding="utf-8")
    debug_print('create url:' + url_example + prepate_url)
    # regex
    # today = datetime.date.today()
    # todaystr = today.strftime("%d.%m.%Y")
    # todaystr = '10.10.2012'
    company_info = {}
    try:
        i, j, page = 1, 1, 1
        time_start = time.time()
        while i <= j:
            params['index'] = page
            prepate_url = parse.urlencode(params, encoding="utf-8")
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
                idss = [tl for tl in ids]
                thread_pages = threading.Thread(target=get_data_allpages, args=(company_info, idss, url_date, regexps, (config['start'], config['end'])))
                thread_pages.daemon = True
                thread_pages.start()
                thread_pages.join()
                # max_sum = order_info(regexps['max_sum'], url_info + lp)
                # garant = order_info(regexps['garant'], url_info + lp)
                # print(lp, max_sum, garant, url_fullinfo + lp)
                # print(link_in_page)
            else:
                i += 1
                print("Error getURL")
            page += 1
        print('found:', len(company_info))
        print("delta time = ", time.time() - time_start)
    except (ValueError, IndexError) as e:
        print("Error: {0}".format(e))

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print('Press Ctrl+C, Bye')