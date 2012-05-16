from datetime import datetime
from django.utils.safestring import mark_safe
import ttp


def enrich_api_result(tweet_list, exclude_replies=False, max_url_length=60, limit=None):
    """
    Apply the local presentation logic to the fetched data.
    """
    tweets = []
    for status in tweet_list:
        if exclude_replies and status.GetInReplyToUserId() is not None:
            continue

        # Add expando attributes to the status
        # mark_safe() should perhaps happen in the templatetag layer, but for the purpose it's good enough here.
        status.html = mark_safe(urlize_status(status, max_url_length=max_url_length))
        status.created_at_as_datetime = datetime.fromtimestamp(status.created_at_in_seconds) if status.created_at else None
        tweets.append(status)

    if limit:
        tweets = tweets[:limit]

    return tweets


def urlize_status(status, max_url_length=60):
    """
    Convert the twitter status to HTML.
    This also expands the links and retweet status.
    """
    text = expand_twitter_status_text(status, max_url_length=max_url_length)
    return urlize_twitter_text(text, max_url_length=max_url_length)


def urlize_twitter_text(text, max_url_length=60):
    """
    Turn #hashtab and @username in a text to Twitter hyperlinks,
    similar to the ``urlize()`` function in Django.
    """
    tweet_parser = ttp.Parser(max_url_length=max_url_length)
    return tweet_parser.parse(text).html


def expand_twitter_status_text(status, max_url_length=60):
    """
    Replace shortened URLs with long URLs in the twitter status, and add the "RT" flag.
    """
    if status.retweeted_status:
        text = u'RT @{user}: {text}'.format(user=status.retweeted_status.user.screen_name, text=status.retweeted_status.text)
        urls = status.retweeted_status.urls
    else:
        text = status.GetText()
        urls = status.urls

    if max_url_length and urls:
        for status_url in urls:
            text = text.replace(status_url.url, status_url.expanded_url)

    return text
