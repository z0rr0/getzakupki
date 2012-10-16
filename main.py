#!/usr/bin/env python3
#-*- coding: utf-8 -*-

import re, time, threading
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
    prepare_func = lambda x: parse.urlencode(x, encoding="utf-8")
    urls = {"base": "http://zakupki.gov.ru/pgz/public/action/search/simple/result?",
        "xml": "http://zakupki.gov.ru/pgz/printForm?type=NOTIFICATION&id=",
        "common": "http://zakupki.gov.ru/pgz/public/action/orders/info/common_info/show?notificationId=",
        "protocol": "http://zakupki.gov.ru/pgz/public/action/orders/info/commission_work_result/show?notificationId=",
    }
    regexps = {'base': re.compile(r"Размещение\s+завершено.*?\((\d+)\)",regex_param),
        'regex_id': re.compile(r'Открытый аукцион в электронной форме.*?showNotificationPrintForm.*?(\d+)\)',regex_param),
        'max_sum': re.compile(r"<maxPriceXml>(.{1,99})</maxPriceXml>",regex_param),
        'garant': re.compile(r"<guaranteeApp>.*?<amount>(.{1,99})</amount>.*?</guaranteeApp>",regex_param),
        'date': re.compile(r"Протокол подведения итогов аукциона.*?от.*?(\d{2}.\d{2}.\d{4})</a>",regex_param)
    }
    params = {'orderName': '', '_orderNameMorphology': 'on', '_orderNameStrict': 'on', 'placingWayType': 'EF', 
        '_placementStages': 'on', '_placementStages': 'on', 
        'placementStages': 'FO', '_placementStages': 'on', '_placementStages': 'on',
        'initiatorFullName': '', 'initiatorId': '', 'priceRange': 'H', 'currencyCode': 'RUB', '_smallBisnes': 'on',
        'index': 1, 'sortField': 'lastEventDate', 'descending': 'true', 'tabName': 'FO', 'lotView': 'false', 
        'pageX': '', 'pageY': ''}
    # NOTE: encoding - optional for this case
    prepate_url = prepare_func(params)
    debug_print('create url: ' + urls['base'] + prepate_url)
    companies = {}
    try:
        pageCount, recordCount, page = 0, 0, config['first']
        time_start = time.time()
        while (page <= config['last']):
            params['index'] = page
            prepate_url = prepare_func(params)
            from_url = getURL(urls['base'] + prepate_url)
            if from_url:
                # NOTE: no need to seach all record
                # refound_base = regexps['base'].search(from_url)
                # allrecord = refound_base.groups()
                ids_str = regexps['regex_id'].findall(from_url)
                # all calculte done in treads
                # tread take: urls, regexps, ids_str, dates, companies
                # thread return all data: companies
                # NOTE: thread realisation
                # thread_pages = threading.Thread(target=get_data_allpages, args=(companies, ids_str, urls, regexps, (config['start'], config['end'])))
                # thread_pages.daemon = True
                # thread_pages.start()
                # wait all threads
                # thread_pages.join()
                print("Done page #{0} from {1}, {2} records".format(page, config['last'], len(ids_str)))
            else:
                print("Error getURL or not found data no page={0}".format(page))
            page += 1
        print("delta time = ", time.time() - time_start)
    except (ValueError, IndexError) as e:
        print("Error: {0}".format(e))

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print('Press Ctrl+C, Bye')