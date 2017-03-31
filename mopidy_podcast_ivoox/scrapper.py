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
        self.basefield = basefield
        self.default = default

    def extract(self, data):
        try:
            raw_value = data.xpath('.' + self.xpath)[0]
            return self.parser(raw_value)
        except:
            return self.default


class Scrapper(object):

    def __init__(self, session=None):
        self._session = session or requests.session()
        self._fieldlist = collections.OrderedDict()
        self.item_selector = '.'  # dot indicates root xpath
        self.declare_fields()

    def declare_fields(self):
        pass

    def add_field(self, name, *args, **kwargs):
        self._fieldlist[name] = Field(*args, **kwargs)

    def clear_fields(self):
        self._fieldlist.clear()

    def scrap(self, url):
        data = self._get_data_from_url(url)
        items = data.xpath(self.item_selector)
        itemlist = [self._populate_item(itemdata)
                    for itemdata in items]
        return itemlist

    def _populate_item(self, itemdata):
        item = {name: field.extract(itemdata)
                for name, field in self._fieldlist.iteritems()
                if field.xpath}

        item_base = {name: field.parser(item[field.basefield])
                     for name, field in self._fieldlist.iteritems()
                     if field.basefield}

        item.update(item_base)
        return item

    def _get_data_from_url(self, url):
        return html.fromstring(self._session.get(url).text)
