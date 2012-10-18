#!/usr/bin/env python3
#-*- coding: utf-8 -*-

import re, time, threading
from urllib import parse
from winners import *

DEBUG = True
CONFIG = "config.conf"
MAX_THREADS = 6

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
    # base dicts
    urls = {"base": "http://zakupki.gov.ru/pgz/public/action/search/simple/result?",
        "xml": "http://zakupki.gov.ru/pgz/printForm?type=NOTIFICATION&id=",
        "common": "http://zakupki.gov.ru/pgz/public/action/orders/info/common_info/show?notificationId=",
        "protocol": "http://zakupki.gov.ru/pgz/public/action/orders/info/commission_work_result/show?notificationId=",
    }
    regexps = {'base': re.compile(r"Размещение\s+завершено.*?\((\d+)\)",regex_param),
        'regex_id': re.compile(r'Открытый аукцион в электронной форме.*?showNotificationPrintForm.*?(\d+)\)',regex_param),
        'max_sum': re.compile(r"<maxPriceXml>(.{1,99})</maxPriceXml>",regex_param),
        'garant': re.compile(r"<guaranteeApp>.*?<amount>(.{1,99})</amount>.*?</guaranteeApp>",regex_param),
        'date': re.compile(r"Протокол подведения итогов аукциона.*?от.*?(\d{2}.\d{2}.\d{4})</a>",regex_param),
        'crean_protocol': re.compile(r"<table><tbody><tr><td><span>\s*Последнее\s+предложение.*?</table>"),
        'find_winner': re.compile(r'<tr.*?iceDatTblRow.*?><td.*?iceDatTblCol.*?><span.*?>(.*?)</span></td><td.*?iceDatTblCol.*?><span.*?>(.*?)</span></td>.*?<span class="iceOutTxt">(\d+)</span></td></tr>'),
    }
    params = {'orderName': '', '_orderNameMorphology': 'on', '_orderNameStrict': 'on', 'placingWayType': 'EF', 
        '_placementStages': 'on', '_placementStages': 'on', 
        'placementStages': 'FO', '_placementStages': 'on', '_placementStages': 'on',
        'initiatorFullName': '', 'initiatorId': '', 'priceRange': 'H', 'currencyCode': 'RUB', '_smallBisnes': 'on',
        'index': 1, 'sortField': 'lastEventDate', 'descending': 'true', 'tabName': 'FO', 'lotView': 'false', 
        'pageX': '', 'pageY': ''}
    # NOTE: encoding - optional for this case
    params['priceRange'] = config['category']
    if DEBUG:
        prepate_url = prepare_func(params)
        debug_print('create url: ' + urls['base'] + prepate_url)
    companies = {}
    try:
        pageCount, recordCount, page = 0, 0, config['first']
        time_start = time.time()
        while (page <= config['last']):
            params['index'] = page
            prepate_url = prepare_func(params)
            from_url = getURLcontent(urls['base'] + prepate_url)
            if from_url:
                # NOTE: no need to seach all record
                # refound_base = regexps['base'].search(from_url)
                # allrecord = refound_base.groups()
                ids_str = regexps['regex_id'].findall(from_url)
                # all calculte done in treads
                # tread take: urls, regexps, ids_str, dates, companies
                # thread return all data: companies
                # NOTE: thread realisation
                for i in ids_str:
                    thread_pages = threading.Thread(target=get_data_page, args=(i, companies, urls, regexps, (config['start'], config['end'])))
                    thread_pages.daemon = True
                    thread_pages.start()
                    # wait all threads
                    thread_pages.join()
                # i = 0
                # while i<len(ids_str):
                #     for_work = ids_str[i:i+MAX_THREADS]
                #     arg_param = (companies, ids_str, urls, regexps, (config['start'], config['end']))
                #     # create threads
                #     thread_pages = threading.Thread(target=get_data_allpages, args=arg_param)
                #     thread_pages.daemon = True
                #     thread_pages.start()
                #     # wait all threads
                #     thread_pages.join()
                #     # next list
                #     i += MAX_THREADS
                recordCount += len(ids_str)
                pageCount += 1
                print("Done page #{0} from {1}, {2} records from {3}".format(page, config['last'], len(ids_str), recordCount))
                print(ids_str)
            else:
                print("Error getURL or not found data no page={0}".format(page))
            page += 1
        print("delta time = ", time.time() - time_start)
        print('found', len(companies))
        print(companies)
    except (ValueError, IndexError) as e:
        print("Error: {0}".format(e))

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print('Press Ctrl+C, Bye')
