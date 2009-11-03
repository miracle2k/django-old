import logging
import urllib
from django.conf import settings
from django.contrib.sites.models import get_current
from django.core import urlresolvers, paginator

class SitemapNotFound(Exception):
    pass

def get_sitemap_url():
    sitemap_url = None
    try:
        # First, try to get the "index" sitemap URL.
        sitemap_url = urlresolvers.reverse('django.contrib.sitemaps.views.index')
    except urlresolvers.NoReverseMatch:
        try:
            # Next, try for the "global" sitemap URL.
            sitemap_url = urlresolvers.reverse('django.contrib.sitemaps.views.sitemap')
        except urlresolvers.NoReverseMatch:
            pass
 
    if sitemap_url is None:
        raise SitemapNotFound("You didn't provide a sitemap_url, and the sitemap URL couldn't be auto-detected.")
 
    return sitemap_url

class Pinger(object):
    logger = None
    name = None
    ping_url = None
    sitemap_url = None
    
    def __init__(self, sitemap_url=None, ping_url=None, domain=None):
        self.domain = domain
        self.sitemap_url = "http://%s%s" % (domain or get_current().domain, sitemap_url or get_sitemap_url())
        if ping_url:
            self.ping_url = ping_url
        self.logger = logging.getLogger("django.contrib.sitemaps.%s" % str(self.__class__.__name__))
    
    def ping(self):
        try:
            if settings.DEBUG:
                self.logger.debug("Pinging %s with sitemap %s..." % (self.name, self.sitemap_url))
            params = urllib.urlencode({'sitemap' : self.sitemap_url})
            u = urllib.urlopen("%s?%s" % (self.ping_url, params))
            if settings.DEBUG:
                self.logger.debug(u.read())
            self.logger.info("Pinged %s with sitemap %s." % (self.name, self.sitemap_url))
        except Exception, e:
            self.logger.error("%s ping failed: %s" % (self.name, e))

class AskPinger(Pinger):
    name = 'Ask'
    ping_url = 'http://submissions.ask.com/ping'

class GooglePinger(Pinger):
    name = 'Google'
    ping_url = 'http://www.google.com/webmasters/tools/ping'

class LiveSearchPinger(Pinger):
    name = 'Live Search'
    ping_url = 'http://webmaster.live.com/ping.aspx'

class YahooPinger(Pinger):
    name = 'Yahoo!'
    ping_url = 'http://search.yahooapis.com/SiteExplorerService/V1/ping'
    
    def ping(self, sitemap_url=None, ping_url=None):
        super(YahooPinger, self).ping()
        
        try:
            base_url = "http://%s/" % (self.domain or get_current().domain)
            if settings.DEBUG:
                self.logger.debug("Pinging %s with base site URL %s..." % (self.name, base_url))
            params = urllib.urlencode({'sitemap' : base_url})
            u = urllib.urlopen("%s?%s" % (self.ping_url, params))
            if settings.DEBUG:
                self.logger.debug(u.read())
            self.logger.info("Pinged Yahoo with base site URL %s." % (base_url))
        except Exception, e:
            self.logger.error("Yahoo base URL ping failed: %s" % e)

def ping_google(sitemap_url=None, ping_url=None, domain=None):
    GooglePinger(sitemap_url=sitemap_url, domain=domain).ping()

def ping_search_engines(sitemap_url=None, domain=None):
    pingers = getattr(settings, 'SITEMAP_PINGERS', [AskPinger, GooglePinger, LiveSearchPinger, YahooPinger])
    for pinger in pingers:
        pinger = pinger(sitemap_url=sitemap_url, domain=domain)
        pinger.ping()

class Sitemap(object):
    # This limit is defined by Google. See the index documentation at
    # http://sitemaps.org/protocol.php#index.
    limit = 50000
    protocol = 'http'

    def __get(self, name, obj, default=None):
        try:
            attr = getattr(self, name)
        except AttributeError:
            return default
        if callable(attr):
            return attr(obj)
        return attr

    def items(self):
        return []

    def location(self, obj):
        return obj.get_absolute_url()

    def _get_paginator(self):
        if not hasattr(self, "_paginator"):
            self._paginator = paginator.Paginator(self.items(), self.limit)
        return self._paginator
    paginator = property(_get_paginator)

    def get_urls(self, page=1):
        current_site = get_current(self.request)
        urls = []
        for item in self.paginator.page(page).object_list:
            loc = "%s://%s%s" % (self.protocol, current_site.domain, self.__get('location', item))
            url_info = {
                'location':   loc,
                'lastmod':    self.__get('lastmod', item, None),
                'changefreq': self.__get('changefreq', item, None),
                'priority':   self.__get('priority', item, None)
            }
            urls.append(url_info)
        return urls

class FlatPageSitemap(Sitemap):
    def items(self):
        current_site = get_current(self.request)
        return current_site.flatpage_set.all()

class GenericSitemap(Sitemap):
    priority = None
    changefreq = None

    def __init__(self, info_dict, priority=None, changefreq=None):
        self.queryset = info_dict['queryset']
        self.date_field = info_dict.get('date_field', None)
        self.priority = priority
        self.changefreq = changefreq

    def items(self):
        # Make sure to return a clone; we don't want premature evaluation.
        return self.queryset.filter()

    def lastmod(self, item):
        if self.date_field is not None:
            return getattr(item, self.date_field)
        return None
