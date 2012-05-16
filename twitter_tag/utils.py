from datetime import datetime
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
        status.html = parse_twitter_text(status, max_url_length=max_url_length)
        status.created_at_as_datetime = datetime.fromtimestamp(status.created_at_in_seconds)
        tweets.append(status)

    if limit:
        tweets = tweets[:limit]

    return tweets


def parse_twitter_text(status, max_url_length=60):
    """
    Convert the twitter status to HTML.
    """
    text = expand_twitter_status_text(status, max_url_length=max_url_length)
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
