# VERSION: 1.00
# AUTHORS: PinkD
# All Copyright To PinkD
from html.parser import HTMLParser

from nova3.novaprinter import prettyPrinter
from nova3.helpers import retrieve_url, download_file
import urllib.request


class btkitty(object):
    url = 'http://btkitty.org/'
    ua = 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/62.0.3202.75 Safari/537.36'
    name = 'bit kitty'
    # Possible categories are ('all', 'movies', 'tv', 'music', 'games', 'anime', 'software', 'pictures', 'books')
    supported_categories = {'all': '0', 'movies': '2', 'music': '3', 'books': '4', 'software': '5', 'pictures': '7'}
    redirect_handler = MyRedirectHandler()

    def __init__(self):
        # some initialization

        request = self._build_request()
        response = urllib.request.urlopen(request)
        while response.url.find('kitty') == -1:
            response = urllib.request.urlopen(request)
        self.url = response.url

    def _build_request(self):
        request = urllib.request.Request(self.url)
        request.add_header('User-Agent', self.ua)
        return request

    def download_torrent(self, info):
        print(download_file(info))

    # DO NOT CHANGE the name and parameters of this function
    # This function will be the one called by nova2.py
    def search(self, what, cat='all'):
        # what is a string with the search tokens, already escaped (e.g. "Ubuntu+Linux")
        # cat is the name of a search category in ('all', 'movies', 'tv', 'music', 'games', 'anime', 'software', 'pictures', 'books')
        # TODO add category
        # cat_id = '0'
        # if cat in self.supported_categories and self.supported_categories[cat] != cat_id:
        #     cat_id = self.supported_categories[cat]
        #     self.redirect_handler.set_id(cat_id)
        parser = MyHtmlParser(self.url)
        request = self._build_request()
        request.method = 'POST'
        request.data = ('keyword=%s' % what).encode()
        response = urllib.request.urlopen(request).read().decode()
        parser.feed(response)
        for item in parser.get_result():
            prettyPrinter(item)
        parser.close()


class MyHtmlParser(HTMLParser):
    def error(self, message):
        raise IOError(message)

    def __init__(self, url):
        HTMLParser.__init__(self)
        self.results = []
        self.url = url
        self.tag_available = False
        self.tag_dt_start = False
        self.current_item = {}
        self.current_seed = ""
        self.current_size = ""
        self.current_magnet_link = ""
        self.current_desc_link = ""
        self.current_name = ""

    def feed(self, data):
        data = data.replace('<b>', '')
        data = data.replace('</b>', '')
        data = data.replace('&nbsp;', ' ')
        HTMLParser.feed(self, data)

    def handle_starttag(self, tag, attrs):
        if tag == "dt":
            self.tag_dt_start = True
            self._save_tmp()
        if tag == "a":
            params = dict(attrs)
            if "href" in params:
                link = params["href"]
                if link.startswith("http"):
                    if "target" in params:
                        self.current_desc_link = link
                        self.tag_available = True
                if link.startswith("magnet:"):
                    self.current_magnet_link = link

    def handle_data(self, data):
        if data.startswith("Size : "):
            self.current_size = data.replace("Size : ", "")
        if data.startswith("Speed : "):
            self.current_seed = data.replace("Speed : ", "")
        if self.tag_available and self.tag_dt_start:
            self.current_name = data

    def handle_endtag(self, tag):
        if tag == "a" and self.tag_available:
            self.tag_available = False
        if tag == "dt":
            self.tag_dt_start = False

    def _save_tmp(self):
        if self.current_name:
            self.current_item["size"] = self.current_size
            self.current_item["name"] = self.current_name
            self.current_item["engine_url"] = self.url
            self.current_item["link"] = self.current_magnet_link
            self.current_item["desc_link"] = self.current_desc_link
            self.current_item["seeds"] = self.current_seed
            self.current_item["leech"] = -1

            self.results.append(self.current_item)

            self.current_item = {}
            self.current_magnet_link = ""
            self.current_desc_link = ""
            self.current_name = ""

    def get_result(self):
        return self.results


class MyRedirectHandler(urllib.request.HTTPRedirectHandler):
    cat_id = '0'

    def redirect_request(self, req, fp, code, msg, headers, newurl):
        newurl.replace('1/0/0.html', ('1/0/%d.html') % self.cat_id)
        return MyRedirectHandler.redirect_request(self, req, fp, code, msg, headers, newurl)

    def set_id(self, cat_id):
        self.cat_id = cat_id
