#!/usr/bin/env python3
#-*- coding: utf-8 -*-

import xlrd3 as xlrd
import xlwt3 as xlwt
from urllib import request, parse
import configparser, re, threading, datetime

def get_config_data(filename):
    """read config file"""
    td = datetime.date.today()
    deltaday = datetime.timedelta(days=3)
    result = {'first': 1, 'last': 10, 'start':td - deltaday, 'end': td, 'category': 'H'}
    config = configparser.ConfigParser()
    try:
        config.read(filename)
        for sec in config.sections():
            if 'first' in config[sec]:
                result['first'] = int(config[sec]['first'])
            if 'last' in config[sec]:
                result['last'] = int(config[sec]['last'])
            if 'start' in config[sec]:
                result['start'] = datetime.datetime.strptime(config[sec]['start'], '%d.%m.%Y')
            if 'end' in config[sec]:
                result['end'] = datetime.datetime.strptime(config[sec]['end'], '%d.%m.%Y')
            if 'category' in config[sec]:
                if result['category'] in ('H', 'I'): result['category'] = config[sec]['category']
    except (ValueError, KeyError, IndexError, TypeError) as er:
        pass
    return result

def getURL(url, code='utf-8'):
    """get data by url, encode to utf-8
    NOTE: may be use
    from urllib.error import URLError
    except (URLError, ValueError, IndexError) as e:
    """
    from_url = False
    try:
        conn = request.urlopen(url)
        if conn.status == 200:
            from_url = conn.read().decode(code)
        else:
            return False
    except Exception as e:
        print("Not connection\nError: {0}".format(e))
    else:
        conn.close()
    return from_url

def prepare_str(input_str):
    """prepare string before using"""
    t = re.compile(r"\s+")
    result = t.sub("", input_str.strip())
    return float(result.replace(",", "."))

def order_info(rg, urlpattern, dataval=None, prep=False, code='utf-8'):
    """find data with regex"""
    if dataval:
        from_url = dataval
    else:
        from_url = getURL(urlpattern, code)
    result = False
    found = rg.search(from_url)
    if not from_url or not found:
        # print("Not date in order_info:", urlpattern)
        return False, False
    result = found.groups()
    try:
        if prep:
            result = prepare_str(result[0])
        else:
            result = result[0]
    except (ValueError, IndexError, TypeError) as e:
        print("Error:", e)
    return result, from_url

def get_data_page(i, companies, urls, regexps, dates):
    datek, protocols = order_info(regexps['date'], urls['protocol'] + i)
    datek = datetime.datetime.strptime(datek, '%d.%m.%Y') if datek else False
    if datek and (dates[0] <= datek <= dates[1]):
        # NOTE: date is good, search any information
        companies[i] = {}
        companies[i]['date'] = datek
        companies[i]['maxsum'], xmlpage = order_info(regexps['max_sum'], urls['xml'] + i, None, True, 'cp1251')
        companies[i]['garant'], xmlpage = order_info(regexps['garant'], urls['xml'] + i, xmlpage, True, 'cp1251')
        # TODO: create winner regex
        # companies[i]['winner'], protocols = order_info(regexps['winner'], urls['protocol'] + i, protocols)
    return 0

def get_data_allpages(companies, ids_str, urls, regexps, dates):
    """start threading for recive companies info"""
    for i in ids_str:
        t = threading.Thread(target=get_data_page, args=(i, companies, urls, regexps, dates))
        t.daemon = True
        t.start()
    return 0

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

            
        