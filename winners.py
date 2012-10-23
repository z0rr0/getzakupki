#!/usr/bin/env python3
#-*- coding: utf-8 -*-

import xlrd3 as xlrd
import xlwt3 as xlwt
from bs4 import BeautifulSoup
from urllib import request, parse
from xml.sax.saxutils import unescape
import configparser, re, threading, datetime
import xml.etree.ElementTree as ET

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

def order_info(rg, urlpattern, dataval=None, prep=False, code='utf-8'):
    """find data with regex"""
    debug_print("call: order_info")
    if dataval:
        from_url = dataval
    else:
        from_url = getURLcontent(urlpattern, code)
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

def get_winner(regexps, from_url):
    """clean table from protocol page"""
    debug_print("call: get_winner")
    lastfound = from_url.rfind("Рейтинг</span></th></tr></thead>")
    if lastfound >0: 
        print('lastfound-',lastfound)
        from_url = from_url[lastfound:]
    # newcontent1 = regexps['clean_prot_other'].sub("", from_url)
    f=open("wf_get_winner.log", 'w')
    f.write(from_url)
    f.close()
    newcontent = regexps['clean_protocol'].sub("", from_url)
    winners = regexps['find_winner'].findall(newcontent)
    for i in winners:
        if i[2] == '1': 
            return {'id': i[0], 'name': unescape(i[1], {
                "&quot;": '"', "&nbsp;": ' ', "&ndash;": '-', "&mdash;": '-', 
                "&laquo;": '"', "&raquo;": '"', "&lsaquo;": '"', "&rsaquo;": '"'})}
    return False

def found_winner(winner):
    print(winner['name'])

def get_data_page(i, companies, urls, regexps, dates, debug=False):
    global DEBUG
    DEBUG = debug
    debug_print("call: get_data_page")
    datek, protocols = order_info(regexps['date'], urls['protocol'] + i)
    datek = datetime.datetime.strptime(datek, '%d.%m.%Y') if datek else False
    if datek and (dates[0] <= datek <= dates[1]):
        # NOTE: date is good, search any information
        print("before get_winner i=", i)
        winner = get_winner(regexps, protocols)
        if winner:
            companies[i] = {}
            companies[i]['date'] = datek
            companies[i]['maxsum'], xmlpage = order_info(regexps['max_sum'], urls['xml'] + i, None, True, 'cp1251')
            companies[i]['garant'], xmlpage = order_info(regexps['garant'], urls['xml'] + i, xmlpage, True, 'cp1251')
            companies[i]['winner'] = winner
            # found_winner(winner)
        # TODO: create winner regex
        # companies[i]['winner'], protocols = order_info(regexps['winner'], urls['protocol'] + i, protocols)
    return 0

def get_data_allpages(companies, ids_str, urls, regexps, dates):
    """start threading for recive companies info"""
    for i in ids_str:
        t = threading.Thread(target=get_data_page, args=(i, companies, urls, regexps, dates))
        t.daemon = True
        t.start()
        # t.join()
    # return 0








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
        self.maxsum, self.garansum = 0, 0
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

    def get_winner(self, form_url, rg):
        soup = BeautifulSoup(form_url)
        tables = soup.find_all('table', attrs={"class": "iceDatTbl"})
        for table in tables:
            trs = table.find_all('tr', attrs={'class': rg})
            for tr in trs:
                needata = tr.find_all('td', recursive=False)
                # winner nubmer == 1
                if needata[5].text == '1':
                    self.winner['id'] = needata[0].text
                    # self.winner['name'] = needata[1].text
                    self.winner['name'] = unescape(needata[1].text, {"&quot;": '"', "&nbsp;": ' ', "&ndash;": '-', "&mdash;": '-', "&laquo;": '"', "&raquo;": '"', "&lsaquo;": '"', "&rsaquo;": '"'})
        return 0

    def get_sums(self, url):
        from_url = getURLcontent(url, 'cp1251')
        if from_url:
            soup = BeautifulSoup(from_url)
            # maxsum = soup.find_all('name')
            # print(soup.prettify())
            # if maxsum: self.maxsum = prepare_str(maxsum)
            # garant
            # garant = soup.find_all('guaranteeApp')
            # complex_garant = False
            # for 
        return 0


            
        