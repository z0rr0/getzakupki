#!/usr/bin/env python3
#-*- coding: utf-8 -*-

import winners, sys, json, re
from urllib import request, parse

DEBUG = True

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

url_example = "http://zakupki.gov.ru/pgz/public/action/search/simple/result?"

params = {'orderName': '', '_orderNameMorphology': 'on', '_orderNameStrict': 'on', 'placingWayType': 'EF', 
    '_placementStages': 'on', '_placementStages': 'on', 
    'placementStages': 'FO', '_placementStages': 'on', '_placementStages': 'on',
    'initiatorFullName': '', 'initiatorId': '', 'priceRange': 'H', 'currencyCode': 'RUB', '_smallBisnes': 'on',
    'index': 1, 'sortField': 'lastEventDate', 'descending': 'true', 'tabName': 'FO', 'lotView': 'false', 
    'pageX': '', 'pageY': ''}
prepate_url = parse.urlencode(params, encoding="utf-8")
debug_print('create url:' + url_example + prepate_url)
regex_all = re.compile(r"Размещение\s+завершено.*?\((\d+)\)",re.IGNORECASE|re.UNICODE|re.DOTALL)
regex_id = re.compile(r'Открытый аукцион в электронной форме.*?showNotificationPrintForm.*?(\d+)\)',re.IGNORECASE|re.UNICODE|re.DOTALL)
try:
    conn = request.urlopen(url_example + prepate_url)
    if conn.status == 200:
        debug_print('Get 200')
        from_url = conn.read().decode('utf-8')
        r = regex_all.search(from_url)
        allrecord = r.groups()
        if len(allrecord):
            debug_print('all record=' + allrecord[0])     
            allrecord = int(allrecord[0])
        ids = regex_id.findall(from_url)
        for i in ids:
            print("id=", i)
except Exception as e:
    print("Not connection\nError: ".format(e))
    # return result
else:
    conn.close()