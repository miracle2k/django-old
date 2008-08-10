from django.conf.urls.defaults import patterns
from django.contrib.syndication import feeds
from django.core.exceptions import ObjectDoesNotExist
from models import Article

class ArticleFeed(feeds.Feed):
    title = "Articles"
    link = "/articles/"

    def items(self):
        return Article.objects.order_by('id')

class ComplexFeed(feeds.Feed):
    def get_object(self, bits):
        if len(bits) != 1:
            raise ObjectDoesNotExist
        return None

urlpatterns = patterns('',
    (r'^feeds/(?P<url>.*)/$', 'django.contrib.syndication.views.feed', {
        'feed_dict': dict(
            complex = ComplexFeed,
            articles = ArticleFeed,
        )}),
)
