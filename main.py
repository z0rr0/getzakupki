#!/usr/bin/env python3
#-*- coding: utf-8 -*-

from winners import *
import re, time 
# import threading
from urllib import parse, request
from platform import system as osdetect

# DEBUG = False # primary
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

def main():
    global DEBUG, CONFIG
    config = get_config_data(CONFIG)
    DEBUG = config['debug']
    # regex_param = re.IGNORECASE|re.UNICODE|re.DOTALL
    regex_param = re.UNICODE|re.DOTALL
    prepare_func = lambda x: parse.urlencode(x, encoding="utf-8")
    # base dicts
    urls = {"base": "http://zakupki.gov.ru/pgz/public/action/search/simple/result?",
        "xml": "http://zakupki.gov.ru/pgz/printForm?type=NOTIFICATION&id=",
        "common": "http://zakupki.gov.ru/pgz/public/action/orders/info/common_info/show?notificationId=",
        "protocol": "http://zakupki.gov.ru/pgz/public/action/orders/info/commission_work_result/show?notificationId=",
        'searchwin': "http://www.etp-micex.ru/organisation/catalog/supplier/fullTitle/{#filltext#}/organisationTypeId/0/",
    }
    regexps = {
        'get_base_page': re.compile(r"showNotificationPrintForm\(\d+\);return false;",regex_param),
        'get_ids': re.compile(r".*?id=(\d+)$", regex_param),
        'get_date1': re.compile(r"^redirectToAE", regex_param),
        'get_date2': re.compile(r"Протокол подведения итогов аукциона.*?\s+от\s+(\d{2}\.\d{2}\.\d{4})", regex_param),
        'get_winner': re.compile(r"iceDatTblRow\d+", regex_param),
        'max_sum': re.compile(r"<maxPriceXml>(.{1,99})</maxPriceXml>",regex_param),
        'garant': re.compile(r"<guaranteeApp>.*?<amount>(.{1,99})</amount>.*?</guaranteeApp>",regex_param),
        # 'garant': re.compile(r"<guaranteeContract>.*?<amount>(.{1,99})</amount>.*?</guaranteeContract>",regex_param),
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
        print('create url: ' + urls['base'] + prepate_url)
    companies = []
    try:
        pageCount, recordCount, page = 0, 0, config['first']
        time_start = time.time()
        print('Start program')
        while (page <= config['last']):
            params['index'] = page
            prepate_url = prepare_func(params)
            from_url = getURLcontent(urls['base'] + prepate_url)
            if from_url:
                ids_str = parser_main_page(regexps['get_ids'], regexps['get_base_page'], from_url)
                if not ids_str:
                    print("Erro in page {}".format(page))
                    continue
                for i in ids_str:
                    print("do record number {0}...".format(i))
                    istr = str(i)
                    ones = Zakupki(i, urls['common'], DEBUG)
                    protocol_page = ones.get_date(urls['protocol'] + istr,regexps['get_date1'], regexps['get_date2'])
                    if ones.necessary_date(config['start'], config['end']):
                        # get winner
                        ones.get_winner(protocol_page, regexps['get_winner'])
                        # get sums
                        ones.get_sums_common(urls['common'] + istr)
                        ones.get_win_data(urls['searchwin'], request.pathname2url)
                        # add new record
                        if ones.garantsum > 0:
                            companies.append(ones)
            else:
                print("Error getURL or not found data no page={0}".format(page))
            page += 1
        print("Finish program, found {0} record for {1} second(s)".format(len(companies), round(time.time() - time_start,2)))
        # sorting
        companies.sort(key=lambda item: item.winner['name'], reverse=True)
        companies.sort(key=lambda item: item.garantsum, reverse=True)
        # print result in MS Excel file
        print_result(companies)
        if osdetect() == 'Windows':
            input("Press any key for close window....")
    except (ValueError, IndexError) as e:
        print("Error: {0}".format(e))

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print('Press Ctrl+C, Bye')
