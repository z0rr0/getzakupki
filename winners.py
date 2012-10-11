#!/usr/bin/env python3
#-*- coding: utf-8 -*-

import xlrd3 as xlrd
import xlwt3 as xlwt
from urllib import request, parse
from urllib.error import URLError
import configparser, re

def getURL(url, code='utf-8'):
    from_url = False
    try:
        conn = request.urlopen(url)
        if conn.status == 200:
            from_url = conn.read().decode(code)
        else:
            return False
    except (URLError, ValueError, IndexError) as e:
        print("Not connection\nError: {0}".format(e))
    else:
        conn.close()
    return from_url

def get_config_data(filename):
    result = {'maxitems': 10}
    config = configparser.ConfigParser()
    try:
        config.read(filename)
        for sec in config.sections():
            if 'maxitems' in config[sec]:
                result['maxitems'] = int(config[sec]['maxitems'])
    except (ValueError, KeyError, IndexError, TypeError) as er:
        pass
    return result

def prepare_str(input_str):
    t = re.compile(r"\s+")
    result = t.sub("", input_str.strip())
    return float(result.replace(",", "."))

def order_info(rg, urlpattern, dataval=None, prep=False, code='utf-8'):
    # max_sum = "http://zakupki.gov.ru/pgz/printForm?type=NOTIFICATION&id=" + str(num)
    # rg = re.compile(r"<td.*?>.*?Начальная \(максимальная\) цена контракта.*?</td>.*?<td.*?>(.{1,15})Российский рубль")
    if dataval:
        from_url = dataval
    else:
        from_url = getURL(urlpattern, code)
    result = False
    found = rg.search(from_url)
    if not from_url or not found: 
        return False
    result = found.groups()
    try:
        if prep:
            result = prepare_str(result[0])
        else:
            result = result[0]
    except (ValueError, IndexError, TypeError) as e:
        print("Error:", e)
    return result


class ZakupkiBase():
    """main base class"""
    def __init__(self, arg):
        self.counter = arg
        self.items = []

    def __repr__(self):
        return "<Zakupki object, {0} items>".format(self.counter)
    def __str__(self):
        return "<Zakupki object, {1} items from {0}>".format(self.counter, len(self.items))
    def __bool__(self):
        valid = True if self.items else False
        return valid

    class Item():
        """docstring for Item"""
        def __init__(self, arg={}):
            keys = arg.keys()
            self.id = arg['id'] if 'id' in keys else None
            self.link = arg['link'] if 'link' in keys else None
            self.name = arg['name'] if 'name' in keys else None
            self.pricemax = arg['pricemax'] if 'pricemax' in keys else None
            self.priceob = arg['priceob'] if 'priceob' in keys else None
            self.winname = arg['winname'] if 'winname' in keys else None
            self.winfull = arg['winfull'] if 'winfull' in keys else None
            self.windate = arg['windate'] if 'windate' in keys else None
            self.wininn = arg['wininn'] if 'wininn' in keys else None
            self.winogrn = arg['winogrn'] if 'winogrn' in keys else None 
            self.winkpp = arg['winkpp'] if 'winkpp' in keys else None 
        def __repr__(self):
            return "<Item object, {0}>".format(self.id)
        def __str__(self):
            return "<Item object, {0}>".format(self.id)
        def __bool__(self):
            valid = True if self.id else False
            return valid

class Zakupki(ZakupkiBase):
    """main class"""
    def __init__(self, arg):
        super().__init__(arg)
        self.arg = arg

    def additem(self, arg):
        self.items.append(self.Item(arg))
        return 0

    def print_items(self):
        j = 1
        for i in self.items:
            print("{0}\t id={1}".format(j, i.id))
            j += 1

            
        