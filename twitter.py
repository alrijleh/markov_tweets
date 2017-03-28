import tweepy
import pickle
import random
import os.path

def authenticate():
    with open("credentials.pickle", "rb") as f:
        credentials = pickle.load(f)

    auth = tweepy.OAuthHandler(credentials["consumer_key"], credentials["consumer_secret"])
    auth.set_access_token(credentials["access_token"], credentials["access_token_secret"])

    api = tweepy.API(auth)
    return api
    
def download_tweets(api):

    all_tweets = []

    new_tweets = api.user_timeline(screen_name = 'realDonaldTrump', count = 100)
    all_tweets.extend(new_tweets)
    max_id = all_tweets[-1].id - 1

    while len(new_tweets) > 0:
        new_tweets = api.user_timeline(screen_name = 'realDonaldTrump', count = 100, max_id = max_id)
        all_tweets.extend(new_tweets)
        max_id = all_tweets[-1].id - 1
        if (max_id == last_max_id):
            break

        print(all_tweets[-1].text)

    return all_tweets
    #with open("tweets.pickle", "wb") as f:
    #    pickle.dump(all_tweets, f)

def print_tweets(tweets):
    for tweet in tweets:
        print("---\n" + " ".join(tweet))

def preprocess(all_tweets):
    tweet_array = []

    for tweet in all_tweets:
        word_list = tweet.split()
        first_word = word_list[0]
        if '@' in first_word and ':' in first_word: #quote
            continue
        if first_word == 'RT': #pseudo retweet
            continue
        word_list = [word for word in word_list if 'http' not in word]
        for word in word_list:
            if 'http' in word:
                continue
            char_pairs = "\"'()[]"
            new_word = word
            if word[-1] != '.': #only do these corrections if not end of a sentance
                if word[0] in char_pairs and word[-1] not in char_pairs:
                    new_word = word[1:]
                if word[-1] in char_pairs and word[0] not in char_pairs:
                    new_word = word[:-2]
        tweet_array.append(word_list)
    return tweet_array

def load_file(filename):
    with open("tweets.txt", "r") as f:
        data = [line.strip() for line in f]
        data = data[:8074] #only tweets after candidacy
        return data

def build_chain(tweet_list):
    word_dict = {}
    for tweet in tweet_list:
        first_word = tweet[0]
        last_word = tweet[-1]
        for word_index in range(len(tweet)):
            current_word = tweet[word_index]
            if current_word is not last_word:
                next_word = tweet[word_index + 1]
                if current_word not in word_dict:
                    word_dict[current_word] = []
                word_dict[current_word].append(next_word)
    return word_dict

def generate_tweet (word_dict):
    key_list = list( word_dict.keys() )

    while True:
        first_word = random.choice ( key_list )
        new_tweet = [first_word]
        while len( " ".join(new_tweet)) < 140:
            current_word = new_tweet[-1]
            next_word = random.choice( word_dict[current_word] )
            new_tweet.append( next_word )      
            if next_word not in key_list:
                #finish tweet if a finisher is found
                return new_tweet
        while len(new_tweet) > 0:
            if new_tweet[-1] not in key_list:
                #ensure last word is a valid finisher
                return new_tweet
            del new_tweet[-1]
            
def postprocess_tweet (new_tweet):
    #Last word punctuation
    last_word_list = list(new_tweet[-1])
    if last_word_list[0] not in "@#" and last_word_list[-1] not in '.,:?!%"\'':
        last_word_list.append('.')
    last_word = ''.join(last_word_list)
    new_tweet[-1] = last_word
    
    #Combine word array to string
    tweet_text = " ".join( new_tweet )
    tweet_text = tweet_text.capitalize()
    
    #Remove lonely quotations & parens
    if tweet_text.count('"') %2 == 1:
        tweet_text = tweet_text.replace('"','')
    if tweet_text.count('(') + tweet_text.count(')') %2 == 1:
        tweet_text = tweet_text.replace('(','')
        tweet_text = tweet_text.replace(')','')

    return tweet_text
    
def watch_for_new_tweet(api):
    with open('tweets.pickle') as f:
        last_id, all_tweets = pickle.load(f)

    latest_tweet = api.user_timeline(screen_name = 'realDonaldTrump', count = 1)
    if latest_tweet.id > last_id:
        return latest_tweet


if __name__ == '__main__':
    tweets = load_file("tweets.txt")
    tweets = preprocess(tweets)
    word_dict = build_chain(tweets)
    while True:
        new_tweet = generate_tweet(word_dict)
        new_tweet = postprocess_tweet(new_tweet)
        print( new_tweet )
        input()
