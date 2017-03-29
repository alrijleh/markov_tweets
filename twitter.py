import tweepy
import time
import pickle
import random
import string
import os.path

def authenticate():
    with open("credentials.pickle", "rb") as f:
        credentials = pickle.load(f)

    auth = tweepy.OAuthHandler(credentials["consumer_key"], credentials["consumer_secret"])
    auth.set_access_token(credentials["access_token"], credentials["access_token_secret"])

    api = tweepy.API(auth)
    return api

def preprocess(tweet):
    tweet = ''.join( filter(lambda x: x in string.printable, tweet) )
    word_list = tweet.split()
    if not word_list:
        return False
    first_word = word_list[0]
    if '@' in first_word and ':' in first_word: #quote
        return False
    if first_word == 'RT': #pseudo retweet
        return False
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
    tweet = word_list
    return tweet

def load_file(filename):
    with open("tweets.txt", "r") as f:
        data = [line.strip() for line in f]

    with open("last_id.txt", "r") as f:
        last_id = int(f.read())

    return data, last_id

def add_to_chain(tweet_list, word_dict):
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
    
def get_new_tweet(api, last_id):
    latest_tweets = api.user_timeline(screen_name = 'realDonaldTrump', count = 20)
    tweets = [tweet.text for tweet in latest_tweets if tweet.id > last_id]
    if tweets:
        return [tweets, latest_tweets[0].id]

    return [False, last_id]

def update_files(tweet, last_tweet_id):
    with open('last_id.txt', 'w') as f:
        f.write(str(last_tweet_id))
    with open('tweets.txt', 'a') as f:
        tweet_text = " ".join( tweet ) + '\r\n'
        f.write(tweet_text)

if __name__ == '__main__':
    api = authenticate()

    old_tweets, last_tweet_id = load_file("tweets.txt")
    old_tweets = [preprocess(tweet) for tweet in old_tweets if preprocess(tweet)]
    word_dict = add_to_chain(old_tweets, {})

    while True: #should be a controlled infinite while loop or something
        new_tweets, last_tweet_id = get_new_tweet(api, last_tweet_id)
        if new_tweets:
            new_tweets = [preprocess(tweet) for tweet in new_tweets if preprocess(tweet)]

            for new_tweet in new_tweets:
                word_dict = add_to_chain([new_tweet], word_dict)
                #update_files(new_tweet, last_tweet_id)

            generated_tweet = generate_tweet(word_dict)
            generated_tweet = postprocess_tweet(generated_tweet)
            api.update_status(generated_tweet, last_tweet_id)
            time.sleep(2)
