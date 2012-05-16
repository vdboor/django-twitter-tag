from __future__ import absolute_import
import logging
from urllib2 import URLError

from django import template
from django.core.cache import cache
from templatetag_sugar.parser import Optional, Constant, Name, Variable
from templatetag_sugar.register import tag
import twitter
from twitter_tag.utils import enrich_api_result


register = template.Library()
logger = logging.getLogger(__name__)


def get_cache_key(*args):
    return 'get_tweets_%s' % ('_'.join([str(arg) for arg in args if arg]))


@tag(register, [Constant("for"), Variable(), Constant("as"), Name(),
                Optional([Constant("exclude"), Variable("exclude")]),
                Optional([Constant("max_url_length"), Variable("max_url_length")]),
                Optional([Constant("limit"), Variable("limit")])])
def get_tweets(context, username, asvar, exclude='', max_url_length=60, limit=None):
    """
    Return the tweets of a given username.
    """
    # The cache exists to return old results when the twitter API reports an error.
    cache_key = get_cache_key(username, asvar, exclude, limit)
    try:
        user_last_tweets = twitter.Api().GetUserTimeline(screen_name=username,
                                                         include_rts=('retweets' not in exclude),
                                                         include_entities=True)
    except (twitter.TwitterError, URLError), e:
        logger.error(str(e))
        context[asvar] = cache.get(cache_key, [])
        return ""

    tweets = enrich_api_result(user_last_tweets, 'replies' in exclude, max_url_length=max_url_length, limit=limit)
    context[asvar] = tweets
    cache.set(cache_key, tweets)
    return ""
