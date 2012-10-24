#!/usr/bin/env python3
#-*- coding: utf-8 -*-

import xlrd3 as xlrd
import xlwt3 as xlwt
import xml.dom.minidom
from bs4 import BeautifulSoup
from urllib import request, parse
from xml.sax.saxutils import unescape
import configparser, re, threading, datetime

DEBUG = False # secondary (primary in main.py)

def debug_print(er, debug=None):
    global DEBUG
    if DEBUG: print(er)

def getURLcontent(url, code='utf-8'):
    """get data by url, encode to utf-8
    NOTE: may be use
    from urllib.error import URLError
    except (URLError, ValueError, IndexError) as e:
    """
    debug_print("call: getURLcontent: " + url)
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

def get_config_data(filename):
    """read config file"""
    td = datetime.datetime.today()
    deltaday = datetime.timedelta(days=3)
    result = {'first': 1, 'last': 10, 'start':td - deltaday, 'end': td, 'category': 'H', 'debug': False}
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
            if 'debug' in config[sec]:
                result['debug'] = config[sec].getboolean('debug')
    except (ValueError, KeyError, IndexError, TypeError) as er:
        pass
    return result

def prepare_str(input_str):
    """prepare string before using"""
    debug_print("call: prepare_str")
    t = re.compile(r"\s+")
    result = t.sub("", input_str.strip())
    return float(result.replace(",", "."))

def getText(nodelist):
    rc = []
    for node in nodelist:
        if node.nodeType == node.TEXT_NODE:
            rc.append(node.data)
    return ''.join(rc)

def parse_kav(nstr):
    rg = re.compile(r'"(.*?)"', re.UNICODE|re.DOTALL)
    name = rg.search(nstr)
    name = name.groups()[0] if name else nstr
    return name

def parser_main_page(r, rg, from_url):
    """get ids from main page"""
    soup = BeautifulSoup(from_url)
    links = soup.find_all('a', attrs={"class": "iceCmdLnk", "onclick": rg})
    result = []
    for link in links:
        try:
            g = r.search(link.attrs['href'])
            result.append(int(g.groups()[0]))
        except (KeyError, ValueError) as e:
            debug_print(e)
            return False
    return result

class ZakupkiBase():
    """main base class"""
    def __init__(self, arg=None):
        self.id = arg
        self.date = None
        self.maxsum, self.garantsum, self.garantMix = 0, 0, 0
        self.winner = {'id': None, 'name': "", 'inn': None}
        self.pages = {'protocol': None, 'info': None, 'xml': None}

    def __repr__(self):
        return "<Zakupki object, id={0}>".format(self.id)
    def __str__(self):
        return "<Zakupki object, id={0}>".format(self.id)
    def __bool__(self):
        valid = True if self.winner['id'] else False
        return valid

class Zakupki(ZakupkiBase):
    """main class"""
    def __init__(self, arg):
        super().__init__(arg)
        self.arg = arg

    def get_date(self, url, rg, r):
        """find date in protocol page"""
        from_url = getURLcontent(url, 'utf-8')
        if from_url:
            soup = BeautifulSoup(from_url)
            links = soup.find_all('a', attrs={"class": "iceOutLnk", "onclick": rg})
            for link in links:
                search_date = r.search(link.text)
                if search_date:
                    self.date = datetime.datetime.strptime(search_date.groups()[0], '%d.%m.%Y')
        return from_url

    def necessary_date(self, date1, date2):
        """check date for interval"""
        if date1.date() <= self.date.date() <= date2.date():
            return True
        return False

    def get_winner(self, from_url, rg):
        """find winnet from table"""
        soup = BeautifulSoup(from_url)
        tables = soup.find_all('table', attrs={"class": "iceDatTbl"})
        for table in tables:
            trs = table.find_all('tr', attrs={'class': rg})
            for tr in trs:
                needata = tr.find_all('td', recursive=False)
                # winner nubmer == 1
                if needata[5].text == '1':
                    self.winner['id'] = needata[0].text
                    # self.winner['name'] = needata[1].text
                    self.winner['name'] = unescape(needata[1].text, {"&quot;": '"', "&nbsp;": ' ', "&ndash;": '-', "&mdash;": '-', "&laquo;": '"', "&raquo;": '"', "&lsaquo;": '"', "&rsaquo;": '"', '«': '"', '»': '"'})
        return 0

    def get_sums_regexp(self, url, rg_sum, rg_garant):
        """get sums with regexps"""
        from_url = getURLcontent(url, 'cp1251')
        if from_url:
            found = rg_sum.search(from_url)
            if found:
                self.maxsum = prepare_str(found.groups()[0])
            found = rg_garant.findall(from_url)
            if found:
                for garant in found:
                    self.garantMix += 1
                    self.garantsum += prepare_str(garant)
        return 0

    def get_sums_xml(self, url):
        """get sums with xml parser"""
        from_url = getURLcontent(url, 'cp1251')
        if from_url:
            # get max sum
            str_data = xml.dom.minidom.parseString(from_url.replace('encoding="windows-1251"', 'encoding="utf-8"'))
            tmp = str_data.getElementsByTagName("maxPriceXml")[0]
            self.maxsum = prepare_str(getText(tmp.childNodes))
            # get garant sums
            tmp = str_data.getElementsByTagName("guaranteeApp")
            self.garantMix = len(tmp)
            for t in tmp:
                garant_amount = t.getElementsByTagName("amount")[0]
                self.garantsum += prepare_str(getText(garant_amount.childNodes))
        return 0

    def get_win_data(self, url, func):
        """get winner data"""
        # newurl = func(url.replace("{#filltext#}", parse_kav(self.winner['name'])))
        newurl = url.replace("{#filltext#}", func(self.winner['name']))
        if not self.get_win_data_child(newurl):
            print('short')
            self.get_win_data_child(url.replace("{#filltext#}", func(parse_kav(self.winner['name']))))
        return 0

    def get_win_data_child(self, url):
        from_url = getURLcontent(url)
        if from_url:
            soup = BeautifulSoup(from_url)
            tables = soup.find_all('table', attrs={"class": "grid grid-standard"})
            if tables:
                trs = tables[0].find_all('tr', attrs={'id': re.compile(r"rowId-\d+")})
                for tr in trs:
                    needata = tr.find_all('td', recursive=False)
                    print("ft=", needata[0].text)
                    return needata[0].text
        return False
        