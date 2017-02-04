import tweepy
import pickle

def download_tweets():
    with open("credentials.pickle", "rb") as f:
        credentials = pickle.load(f)

    auth = tweepy.OAuthHandler(credentials["consumer_key"], credentials["consumer_secret"])
    auth.set_access_token(credentials["access_token"], credentials["access_token_secret"])

    all_tweets = []

    api = tweepy.API(auth)

    new_tweets = api.user_timeline(screen_name = 'realDonaldTrump', count = 100)
    all_tweets.extend(new_tweets)
    max_id = all_tweets[-1].id - 1

    while len(new_tweets) > 0:
        new_tweets = api.user_timeline(screen_name = 'realDonaldTrump', count = 100, max_id = max_id)
        all_tweets.extend(new_tweets)
        max_id = all_tweets[-1].id - 1

        print(all_tweets[-1].text)

    with open("tweets.pickle", "wb") as f:
        pickle.dump(all_tweets, f)
