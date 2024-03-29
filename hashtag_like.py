#!/usr/bin/env python

"""
Likes tweets with a certain hashtag
"""

# imports
import os, time, json
from sys import exit
from urlparse import urlparse
from contextlib import contextmanager
import tweepy
import backoff

# import exceptions
from urllib2 import HTTPError

def log(**kwargs):
    print ' '.join( "{0}={1}".format(k,v) for k,v in sorted(kwargs.items()) )


@contextmanager
def measure(**kwargs):
    start = time.time()
    status = {'status': 'starting'}
    log(**dict(kwargs.items() + status.items()))
    try:
        yield
    except Exception, e:
        status = {'status': 'err', 'exception': "'{0}'".format(e)}
        log(**dict(kwargs.items() + status.items()))
        raise
    else:
        status = {'status': 'ok', 'duration': time.time() - start}
        log(**dict(kwargs.items() + status.items()))



def validate_env():
    keys = [
        'TW_USERNAME',
        'TW_CONSUMER_KEY',
        'TW_CONSUMER_SECRET',
        'TW_ACCESS_TOKEN',
        'TW_ACCESS_TOKEN_SECRET',
		'TW_Like_Min',
		'TW_HashTag_Search'
        ]

    # Check for missing env vars
    for key in keys:
        v = os.environ.get(key)
        if not v:
            log(at='validate_env', status='missing', var=key)
            raise ValueError("Missing ENV var: {0}".format(key))

    # Log success
    log(at='validate_env', status='ok')

def fav_tweet(api,tweet,like_min):
	"""Attempt to fav a tweet and return True if successful"""

	#QA: don't like if too low
	if tweet.favorite_count < like_min:
		log(at='filter', reason='too unpopular', tweet=tweet.favorite_count)
		return

	# sometimes this raises TweepError even if reply.favorited
	# was False
	try:
		api.create_favorite(id=tweet.id)
	except tweepy.TweepError, e:
		log(at='fav_error', tweet=tweet.id, klass='TweepError', msg="'{0}'".format(str(e)))
		return False

	log(at='favorite', tweet=tweet.id)
	return True

@backoff.on_exception(backoff.expo, tweepy.TweepError, max_tries=8)

def fetch_hashtag_tweets(api,target_hashtag):
    """Fetch tweets with hashtag from twitter"""
    with measure(at='fetch_hashtag'):
        hashtag_tweets = api.search(target_hashtag,count=100)
    return hashtag_tweets

def fetch_timeline_tweets(api):
	timeline_tweets = api.home_timeline(count=50,exclude_replies='true')
	return timeline_tweets
	
	
def main():
	log(at='main')
	main_start = time.time()



	owner_username    = 'CoffinRotVR'
	username          = 'CoffinRotVR'
	consumer_key      = 'HkhVMRqpOWB0ZjROrXgrmTiWS'
	consumer_secret   = '9UEYoUq0eeQEsh9HYtMpOZmLVmVVv2XSRZcJdYGQgB58v1Gfad'
	access_key        = '1016807309987778560-INAuq1xeAp2kGwIceYupSExzsez2r2'
	access_secret     = 'GtHYIXFXbRLd0kuiuikHjecughIPnjIIUI9nseVydSWy1'
	like_min	= 6
	like_min_timeline = 20
	target_hashtag_one    = 'indiedev'
	target_hashtag_two = 'madewithunity'

	auth = tweepy.OAuthHandler(consumer_key=consumer_key,
		consumer_secret=consumer_secret)
	auth.set_access_token(access_key, access_secret)

	api = tweepy.API(auth_handler=auth, retry_count=3)
	tweet_Search = fetch_hashtag_tweets(api,target_hashtag_one)


	for tweet in tweet_Search:

		try:
			fav_tweet(api,tweet,like_min)
		except HTTPError, e:
			log(at='rt_error', klass='HTTPError', code=e.code(), body_size=len(e.read()))
			debug_print(e.code())
			debug_print(e.read())
		except Exception, e:
			log(at='rt_error', klass='Exception', msg="'{0}'".format(str(e)))
			raise
			
	tweet_Search = fetch_hashtag_tweets(api,target_hashtag_two)


	for tweet in tweet_Search:

		try:
			fav_tweet(api,tweet,like_min)
		except HTTPError, e:
			log(at='rt_error', klass='HTTPError', code=e.code(), body_size=len(e.read()))
			debug_print(e.code())
			debug_print(e.read())
		except Exception, e:
			log(at='rt_error', klass='Exception', msg="'{0}'".format(str(e)))
			raise
			
	timeline_Search = fetch_timeline_tweets(api)
	
	# for tweet in timeline_Search:
		# try:
			# fav_tweet(api,tweet,like_min_timeline)
		# except HTTPError, e:
			# log(at='rt_error', klass='HTTPError', code=e.code(), body_size=len(e.read()))
			# debug_print(e.code())
			# debug_print(e.read())
		# except Exception, e:
			# log(at='rt_error', klass='Exception', msg="'{0}'".format(str(e)))
			# raise

	log(at='finish', status='ok', duration=time.time() - main_start)

if __name__ == '__main__':
    # set up rollbar
    rollbar_configured = False
    rollbar_access_key = os.environ.get('ROLLBAR_ACCESS_KEY')
    if rollbar_access_key:
        import rollbar
        rollbar.init(rollbar_access_key, 'production')
        rollbar_configured = True

    try:
        main()
    except KeyboardInterrupt:
        log(at='keyboard_interrupt')
        quit()
    except:
        if rollbar_configured:
            rollbar.report_exc_info()
        raise

