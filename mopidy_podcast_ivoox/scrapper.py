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

    def extract_from_data(self, data):
        input_list = data.xpath(self.xpath)
        return self.parse_input(zip(input_list))

    def parse_input(self, input_list):
        self.value_list = [self.parser(*input_args)
                           for input_args in input_list]
        return self.value_list


class Scrapper(object):

    def __init__(self, session=None):
        self.fieldlist = collections.OrderedDict()
        self.session = session or requests.session()
        self.declare_fields()

    def declare_fields(self):
        pass

    def add_field(self, name, *args, **kwargs):
        self.fieldlist[name] = Field(*args, **kwargs)

    def clear_fields(self):
        self.fieldlist.clear()

    def populate_from_data(self, data):
        for field in self.fieldlist.itervalues():
            if field.xpath:
                field.extract_from_data(data)
            elif field.basefield:
                base_values = [self.fieldlist[name].value_list
                               for name in field.basefield]

                field.parse_input(zip(*base_values))

    def populate_itemlist(self):
        nitems = max(len(field.value_list)
                     for field in self.fieldlist.itervalues())
        self.itemlist = [{key: None for key in self.fieldlist.iterkeys()}
                         for i in xrange(nitems)]
        for name, field in self.fieldlist.iteritems():
            for i, value in enumerate(field.value_list):
                self.itemlist[i].update({name: value})

        return self.itemlist

    def get_data_from_url(self, url):
        return html.fromstring(self.session.get(url).text)

    def process_output(self, output):
        return output

    def scrap(self, url):
        data = self.get_data_from_url(url)
        self.populate_from_data(data)
        self.populate_itemlist()
        return self.process_output(self.itemlist)

    def formatted_output(self):
        for i, itemdict in enumerate(self.itemlist):
            print '[{0:2d}]'.format(i)
            for item, value in itemdict.iteritems():
                print '\t {0}: {1!r}'.format(item, value)
