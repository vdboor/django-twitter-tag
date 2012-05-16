from __future__ import absolute_import
import logging
from hashlib import md5
from urllib2 import URLError

from django import template
from django.core.cache import cache
from django.utils.safestring import mark_safe
from templatetag_sugar.parser import Optional, Constant, Name, Variable
from templatetag_sugar.register import tag
import twitter
from twitter_tag.utils import enrich_api_result, urlize_twitter_text


register = template.Library()
logger = logging.getLogger(__name__)


def get_cache_key(*args):
    return 'get_tweets_%s' % ('_'.join([str(arg) for arg in args if arg]))


def get_search_cache_key(term, *args):
    return 'get_tweets_{term}_{args}'.format(term=md5(term).hexdigest(), args='_'.join([str(arg) for arg in args if arg]))


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


@tag(register, [Variable(), Constant("as"), Name(),
                Optional([Constant("language"), Variable("lang")]),
                Optional([Constant("exclude"), Variable("exclude")]),
                Optional([Constant("max_url_length"), Variable("max_url_length")]),
                Optional([Constant("limit"), Variable("limit")])])
def search_tweets(context, search_query, asvar, lang='', exclude='', max_url_length=60, limit=None):
    """
    Search for status messages which contain a given string.
    """
    # The cache exists to return old results when the twitter API reports an error.
    cache_key = get_search_cache_key(search_query, asvar, exclude, limit)
    if 'retweets' in exclude:
        search_query += "+exclude:retweets"

    try:
        found_tweets = twitter.Api().GetSearch(term=search_query, per_page=limit, lang=lang, query_users=False)
    except (twitter.TwitterError, URLError), e:
        logger.error(str(e))
        context[asvar] = cache.get(cache_key, [])
        return ""

    tweets = enrich_api_result(found_tweets, 'replies' in exclude, max_url_length=max_url_length, limit=limit)
    context[asvar] = tweets
    cache.set(cache_key, tweets)
    return ""


@register.filter
def urlize_twitter(text):
    """
    Replace #hashtag and @username references in a tweet with HTML text.
    """
    return mark_safe(urlize_twitter_text(text))
