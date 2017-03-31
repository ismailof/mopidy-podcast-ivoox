import requests
import collections
from lxml import html


class Field(object):

    def __init__(self,
                 xpath=None, basefield=None,
                 parser=None, default=None):

        self.xpath = xpath
        self.value_list = []
        self.parser = parser or (lambda x: x)
        self.basefield = basefield if isinstance(basefield, list) \
            else [basefield]
        self.default = default

    def parse_input(self, input_list):
        self.value_list = [self.parser(*input_args)
                           for input_args in input_list]
        return self.value_list


class Scrapper(object):

    def __init__(self, session=None):
        self._session = session or requests.session()            
        self._fieldlist = collections.OrderedDict()
        self._itemlist = []
        self.item_selector = None        
        self.declare_fields()

    def declare_fields(self):
        pass

    @property
    def itemlist(self):
        return self._itemlist

    def add_field(self, name, *args, **kwargs):
        self._fieldlist[name] = Field(*args, **kwargs)

    def clear_fields(self):
        self._fieldlist.clear()

    def clear_items(self):
        self._itemlist.clear()
        
    def populate_from_data(self, data):
        for field in self._fieldlist.itervalues():
            if field.xpath:            
                input_list = data.xpath(field.xpath)
            
            elif field.basefield:
                input_list = [self._fieldlist[name].value_list
                               for name in field.basefield]                

            field.parse_input(zip(input_list))
                
    def populate_itemlist(self):
        nitems = max(len(field.value_list)
                     for field in self._fieldlist.itervalues())
        self._itemlist = [{name: field.default
                          for name, field in self._fieldlist.iteritems()}
                         for i in xrange(nitems)]
        for name, field in self._fieldlist.iteritems():
            for i, value in enumerate(field.value_list):
                self._itemlist[i].update({name: value})

        return self._itemlist

    def get_data_from_url(self, url):
        return html.fromstring(self._session.get(url).text)

    def scrap(self, url):
        data = self.get_data_from_url(url)
        self.populate_from_data(data)
        self.populate_itemlist()
        return self._itemlist
