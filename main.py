#!/usr/bin/env python3
#-*- coding: utf-8 -*-

import sys, json, re
from urllib import request, parse

# orderName - 
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

url_example = "http://zakupki.gov.ru/pgz/public/action/search/simple/run?"

params = {'orderName': '', '_orderNameMorphology': 'on', '_orderNameStrict': 'on', 'placingWayType': 'EF', 
    '_placementStages': 'on', '_placementStages': 'on', 
    'placementStages': 'FO', '_placementStages': 'on', '_placementStages': 'on',
    'initiatorFullName': '', 'initiatorId': '', 'priceRange': 'H', 'currencyCode': 'RUB', '_smallBisnes': 'on',
    'index': 1, 'sortField': 'lastEventDate', 'descending': 'true', 'tabName': 'FO', 'lotView': 'false', 
    'pageX': '', 'pageY': ''}
prepate_url = parse.urlencode(params, encoding="utf-8")
# print(url_example + prepate_url)
regex = re.compile("Размещение завершено \((\d{1,})\)",re.IGNORECASE|re.UNICODE)
try:
    conn = request.urlopen(url_example + prepate_url)
    if conn.status == 200:
        print('Get 200')
        from_url = conn.read().decode('utf-8')
        r = regex.search(from_url)
        allrecord = r.groups()
        if len(allrecord):
            allrecord = int(allrecord[0])
        print(allrecord)       
except Exception as e:
    print("Not connection\nError: ".format(e))
    # return result
else:
    conn.close()