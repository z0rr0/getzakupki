#!/usr/bin/env python3
#-*- coding: utf-8 -*-

# import xlrd3 as xlrd
import xlwt3 as xlwt
import http.client
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

def short_url(url):
    """get short url"""
    if len(url) > 255:
        headers = {"Content-type": "application/x-www-form-urlencoded", "Accept": "text/plain"}
        params = parse.urlencode({'url': url})
        conn = http.client.HTTPConnection("clck.ru")
        conn.request("POST", "/--", params, headers=headers)
        res = conn.getresponse()
        if res.status == 200:
            link = res.read()
            return link.decode('utf-8')
    return url

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
    rg1 = re.compile(r'"(.*?)"', re.UNICODE|re.DOTALL)
    rg2 = re.compile(r"'(.*?)'", re.UNICODE|re.DOTALL)
    name = rg1.search(nstr)
    if name:
        return name.groups()[0]
    else:
        name = rg2.search(nstr)
        if name:
            return name.groups()[0]
    return nstr

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
    else:
        debug_print("Call 'parser_main_page', dot found data by html-parser")
    return result

def print_result(collections=None):
    file_name = "excel_" + datetime.datetime.now().strftime("%Y-%m-%d_%H%M%S") + ".xls"
    wb = xlwt.Workbook()
    ws = wb.add_sheet('0')
    headers = ['п/н', 'Название', 'Дата', 'Ссылка', 'Начальная цена контракта', 
        'Размер обеспечения', 'Несколько заказчиков', 'Победитель', 'Кол-во, ссылка', 
        'Регион', 'Город', 'Телефон', 'ИНН', 'КПП', 'ОГРН']
    ezxf = xlwt.easyxf
    font0, font1, font2, font3 = xlwt.Font(), xlwt.Font(), xlwt.Font(), xlwt.Font()
    style0, style1, style2, style3 = xlwt.XFStyle(), xlwt.XFStyle(), xlwt.XFStyle(), xlwt.XFStyle()

    style4 = ezxf("align: wrap on, vert centre, horiz left")

    font0.name = 'Times New Roman'
    font0.bold = True
    style0.font = font0

    font1.bold = False
    style1.font = font1
    style1.num_format_str = '# ### ##0.00'

    font2.colour_index = 4
    style2.font = font2

    style3.num_format_str = "DD.MM.YYYY"
    style3.font = font3

    col, row = 0, 0
    for head in headers:
        ws.write(row, col, head, style0)
        col += 1
    n = "HYPERLINK"
    row += 1
    for colecttion in collections:
        col = 0
        ws.write(row, col, row)
        col += 1
        ws.write(row, col, colecttion.name, style4) 
        col += 1
        ws.write(row, col, colecttion.date, style3)
        col += 1
        ws.write(row, col, xlwt.Formula(n + '("{0}";"{1}")'.format(colecttion.url, colecttion.id)), style2)
        col += 1
        ws.write(row, col, colecttion.maxsum, style1)
        col += 1
        ws.write(row, col, colecttion.garantsum, style1)
        col += 1
        mix = 'да' if colecttion.garantMix > 1 else 'нет'
        ws.write(row, col, mix)
        col += 1
        ws.write(row, col, colecttion.winner['name'], style4)
        col += 1
        links = 'один' if colecttion.winner['urls'] == 1 else links = 'поиск'
        urls = colecttion.winner['surls']
        ws.write(row, col, xlwt.Formula(n + '("{0}";"{1}")'.format(urls, links)), style2)
        col += 1
        ws.write(row, col, colecttion.winner['region'])
        col += 1
        ws.write(row, col, colecttion.winner['city'])
        col += 1
        ws.write(row, col, colecttion.winner['phone'])
        col += 1
        ws.write(row, col, colecttion.winner['inn'])
        col += 1
        ws.write(row, col, colecttion.winner['kpp'])
        col += 1
        ws.write(row, col, colecttion.winner['ogrn'])
        row += 1
    wb.save(file_name)
    return 0

class ZakupkiBase():
    """main base class"""
    def __init__(self, arg=None, url=""):
        self.id = arg
        self.url = url + str(self.id)
        self.date = None
        self.name = ""
        self.maxsum, self.garantsum, self.garantMix = 0, 0, 0
        self.winner = {'id': None, 'name': "", 'urls': 0, 'surls': None, 
            'inn': None, 'ogrn': None, 'kpp': None, 'phone': None, 'region': None, 'city': None}
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
    def __init__(self, arg, url, debug):
        global DEBUG
        super().__init__(arg, url)
        self.arg = arg
        DEBUG = debug

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
        if self.date and (date1.date() <= self.date.date() <= date2.date()):
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
                else:
                    debug_print("Call 'get_winner', dot found winner by html-parser")
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
            else:
                debug_print("Call 'get_sums_regexp', dot found from_url by regexp")
        else:
            debug_print("Call 'get_sums_regexp', dot found from_url by getURLcontent")
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
            # get name
            tmp = str_data.getElementsByTagName("subject")[0]
            self.name = getText(tmp.childNodes)
        else:
            debug_print("Call 'get_sums_xml', dot found from_url by getURLcontent")
        return 0

    def get_sums_common(self, url):
        """get sums with html parser"""
        from_url = getURLcontent(url)
        if from_url:
            soup = BeautifulSoup(from_url)
            table = soup.find('table', attrs={"class": "orderInfo", "cellspacing": "0", "cellpadding": "0"})
            trs = table.find_all('tr')
            for tr in trs:
                label = tr.find('label', attrs={"class": "iceOutLbl"})
                if label:
                    if label.text.find("Размер обеспечения исполнения контракта") > 0:
                        span = tr.find('span', attrs={"class": "iceOutTxt"})
                        if span:
                            self.garantsum += prepare_str(span.text)
                            self.garantMix += 1
                    elif label.text.find("Начальная (Максимальная) цена контракта") > 0:
                        span = tr.find('span', attrs={"class": "iceOutTxt"})
                        if span:
                            self.maxsum += prepare_str(span.text)
                    elif label.text.find("Краткое наименование аукциона") > 0:
                        span = tr.find('span', attrs={"class": "iceOutTxt"})
                        self.name = span.text.strip()
        else:
            debug_print("Call 'get_sums_xml', dot found from_url by getURLcontent")
        return 0

    def get_win_data(self, url, func):
        """get winner data"""
        winner_data = self.get_win_data_child(url.replace("{#filltext#}", func(self.winner['name'])))
        if not winner_data:
            debug_print('not found by name: 1 ')
            winner_data = self.get_win_data_child(url.replace("{#filltext#}", func(parse_kav(self.winner['name']))))
            if not winner_data:
                debug_print('not found by name: 2 ({}) '.format(self.winner['name']))
        return 0

    def get_win_data_child(self, url):
        from_url = getURLcontent(url)
        self.winner['surls'] = short_url(url)
        if from_url:
            soup = BeautifulSoup(from_url)
            table = soup.find('table', attrs={"class": "grid grid-standard"})
            if table:
                trs = table.find_all('tr', attrs={'id': re.compile(r"rowId-\d+")})
                self.winner['urls'] = len(trs)
                try:
                    if self.winner['urls'] == 1:
                        needata = trs[0].find('a')
                        surls = 'http://www.etp-micex.ru' + needata.get('href')
                        self.winner['surls'] = short_url(surls)
                        self.get_add_wininfo(self.winner['surls'])
                        print('INN-',self.winner['inn'])
                        return self.winner['surls']
                except IndexError as er:
                    debug_print("call get_win_data_child: error in html parser")
                    return 0
        else:
             debug_print("Call 'get_win_data_child', dot found from_url by getURLcontent")
        return False

    def get_add_wininfo(self, url):
        from_url = getURLcontent(url)
        if from_url:
            soup = BeautifulSoup(from_url)
            fieldset = soup.find("fieldset", attrs={'id': "fieldset-mainData"})

            inn = fieldset.find("span", attrs={"id": "mainData-inn", "class": "formInfo"})
            ogrn = fieldset.find("span", attrs={"id": "mainData-ogrn", "class": "formInfo"})
            kpp = fieldset.find("span", attrs={"id": "mainData-kpp", "class": "formInfo"})
            phone = fieldset.find("span", attrs={"id": "mainData-telephone", "class": "formInfo"})
            if inn: self.winner['inn'] = inn.text
            if ogrn: self.winner['ogrn'] = ogrn.text
            if kpp: self.winner['kpp'] = kpp.text
            if phone: self.winner['phone'] = phone.text

            fieldset = soup.find("fieldset", attrs={'id': "fieldset-placement"})
            region = fieldset.find("span", attrs={"id": "placement-subjectRf", "class": "formInfo"})
            city = fieldset.find("span", attrs={"id": "placement-cityOrArea", "class": "formInfo"})
            if region: self.winner['region'] = region.text
            if city: self.winner['city'] = city.text
        return 0
        