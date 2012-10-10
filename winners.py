#!/usr/bin/env python3
#-*- coding: utf-8 -*-

import xlrd3 as xlrd
import xlwt3 as xlwt

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

            
        