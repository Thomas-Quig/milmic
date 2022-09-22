from cProfile import label
from dotenv import load_dotenv
from datetime import datetime
import tweepy
import json, argparse, os
import matplotlib.pyplot as plt
import numpy as np

# EVENTUALLY MOVE TO CONFIG FILE
config = {
    # Impact Weights
    "like_weight": 1,
    "retweet_weight": 5,
    "quotetweet_weight": 10,
    "reply_weight": 5,
    "followers_weight": 1,
    "tweets_weight": 1
}

DEBUG = True

api = ...
args = ...

class Tweet(object):
    def __init__(self, author = None, content = None, date = None, region = None, likes = None, replies = None, retweets = None, quotetweets = None, attachment = None, url = None, tweet_obj=None, json_obj=None, id=None, tweet_type=None, get_attachments=True):
        if url != None:
            if api == ...:
                raise(Exception('API not initialized'))
            self.url = url
            self.from_link(api, url)
        if tweet_obj != None:
            self.from_tweet(tweet_obj,get_attachments)
        elif json_obj != None:
            self.json_obj = json_obj
            self.from_json()
        elif tweet_obj == None and url == None and json_obj == None:
            self.content = content          # content of tweet, string
            self.date = date                # date of tweet, datetime
            self.author = author            # handle of tweet's poster, string
            self.likes = likes              # number of likes, int
            self.replies = replies          # number of replies, int
            self.retweets = retweets        # number of retweets, int
            self.quotetweets = quotetweets  # number of quoted tweets, int
            self.region = region            # region of tweet, string
            self.attachment = attachment    # attachment of tweet, object (image, video, image album etc.), link or list of links
            self.id = id                    # id of tweet, string
            self.tweet_type = tweet_type    # type of tweet, string

    def impact(self):
        return self.likes * config['like_weight'] + self.retweets * config['retweet_weight'] + self.quotetweets * config['quotetweet_weight'] + self.replies * config['reply_weight']

    def to_dict(self):
        return {
            'content': self.content,
            'date': self.date,
            'author': self.author,
            'likes': self.likes,
            'replies': self.replies,
            'retweets': self.retweets,
            'quotetweets': self.quotetweets,
            'region': self.region,
            'attachment': self.attachment,
            'id': self.id,
            'tweet_type': self.tweet_type
        }

    def to_json(self):
        return json.dumps(self.to_dict(),default=str)

    def from_json(self):
        json_dict = self.json_obj
        self.content = json_dict['content']
        self.date = json_dict['date']
        self.author = json_dict['author']
        self.likes = json_dict['likes']
        self.replies = json_dict['replies']
        self.retweets = json_dict['retweets']
        self.quotetweets = json_dict['quotetweets']
        self.region = json_dict['region']
        self.attachment = json_dict['attachment']
        self.id = json_dict['id']
        self.tweet_type = json_dict['tweet_type']

    def from_tweet(self, tweet, get_attachments=True):
        # write tweet to json file
        data = tweet['data']
        includes = tweet['includes']
        self.content = data['text']
        self.date = data['created_at']
        self.author = {'username': includes['users'][0]['username'], 'id': data['author_id']}
        self.likes = data['public_metrics']['like_count']
        self.replies = data['public_metrics']['reply_count']
        self.retweets = data['public_metrics']['retweet_count']
        self.quotetweets = data['public_metrics']['quote_count']
        self.region = data.get('geo', "None")
        self.id = str(data['id'])

        #print(includes['media'])
        #print(includes['media'])
        #print(type(includes['media'][0]))
        #print([dict(attachment) for attachment in includes['media']])
        if get_attachments:
            self.attachment = [{'type':attachment['type'],'url':attachment.get('url','')} for attachment in includes['media']]
        else:
            #parse urls from tweet
            #print([field for field in data])
            if data.get('entities', None) != None:
                self.attachment = [{'type':'photo' if 'photo' in x['expanded_url'] else 'video' if 'video' in x['expanded_url'] else 'url','url':x['expanded_url']} for x in data.get('entities',{}).get('urls',[])]
            else:
                self.attachment = []

        if data['referenced_tweets'] == None:
            self.tweet_type = 'original'
        else:
            #print(data['referenced_tweets'])
            if type(data['referenced_tweets']) == list:
                self.tweet_type = data['referenced_tweets'][0]['type']
            else:
                self.tweet_type = data['referenced_tweets']['type']

    # gets a tweet from the API and returns it as a tweet object
    def from_link(self, api, url):
        print("Getting tweet from link...")
        # get the tweet id from the url
        tweet_id = url.split('/')[-1]
        response = api.get_tweet(f'{tweet_id}',expansions=['author_id','attachments.media_keys'], tweet_fields=['attachments','author_id','public_metrics','text','geo','created_at','in_reply_to_user_id','referenced_tweets'], user_fields=['username','name'], media_fields=['url'])
        if response.data == None:
            print("ERROR:", response.errors[0]['detail'])
            self.tweet_type = None
            return
        tweet = {'data': response[0],'includes': response[1]}
        self.from_tweet(tweet)
        return

    def __str__(self):
        return f'@{self.author["username"]}\n{self.content}\n{self.date} from {self.region}\nLikes: {self.likes} Retweets: {self.retweets} Quote Tweets: {self.quotetweets}\n'

    def __repr__(self):
        return f'----------==TWEET==----------\nAuthor:{self.author["username"]}\nContent:{self.content}\nDate:{self.date}\nRegion:{self.region}\nReplies:{self.replies}\nLikes:{self.likes}\nRetweets:{self.retweets}\nQuote_Tweets:{self.quotetweets}\nAttachments:{self.attachment}\n-----------------------------'

    def __eq__(self, other):
        return self.content == other.content and self.date == other.date and self.author == other.author and self.likes == other.likes and self.retweets == other.retweets and self.quotetweets == other.quotetweets and self.region == other.region and self.attachment == other.attachment
    
    def __ne__(self, other):
        return not self.__eq__(other)
    
    def __hash__(self):
        return hash((self.content, self.date, self.handle, self.likes, self.retweets, self.quotetweets, self.region, self.attachment))

    def __lt__(self, other):
        return self.impact() < other.impact()
        
    def __le__(self, other):
        return self.impact() <= other.impact()

    def __gt__(self, other):
        return self.impact() > other.impact()

    def __ge__(self, other):
        return self.impact() >= other.impact()
    
class User(object):
    def __init__(self, handle = None, name = None, bio = None, pfp = None, followers = None, following = None, tweets = None, likes = None, retweets = None, quotetweets = None, replies = None, region = None, creation_date = None, url = None, user_obj = None, json_obj = None, depth=0, id=None):
        if api == ...:
            load_api()
        self.depth = depth
        if url != None:
            if api == ...:
                raise(Exception('API not initialized'))
            self.url = url
            print("Initializing user from link", url)
            self.from_link(api,url)
        if user_obj != None:
            self.from_user(user_obj)
        elif json_obj != None:
            self.json_obj = json_obj
            self.from_json()
        elif user_obj == None and url == None and json_obj == None:
            self.handle = handle                # handle of user, string
            self.name = name                    # name of user, string
            self.bio = bio                      # bio of user, string
            self.pfp = pfp                      # pfp of user, image
            self.followers = {"total":followers,"list":[]}      # number of followers, int
            self.following = {"total":following ,"list":[]}          # number of following, int
            self.tweets = {"total":tweets,"list":[]}            # number of tweets, int
            self.likes = {"total":likes,"list":[]}                  # number of likes, int
            self.retweets = retweets            # number of retweets, int
            self.quotetweets = quotetweets      # number of quote tweets, int TODO REMOVE, not used currently
            self.replies = replies              # number of replies, int
            self.region = region                # region of user, string
            self.creation_date = creation_date  # date of user's creation, datetime
            self.id = id

    def impact(self):
        return self.followers['total'] * config['followers_weight'] + self.tweets['total'] * config['tweets_weight']

    def follower_following_ratio(self):
        return (self.followers['total'] / (self.following['total'] if self.following['total'] > 0 else 1))

    def to_dict(self):
        return {
            'handle': self.handle,
            'name': self.name,
            'bio': self.bio,
            'pfp': self.pfp,
            'followers': self.followers,
            'following': self.following,
            'tweets': self.tweets,
            'likes': self.likes,
            'retweets': self.retweets,
            'quotetweets': self.quotetweets,
            'replies': self.replies,
            'region': self.region,
            'creation_date': self.creation_date,
            'id': self.id,
            'depth': self.depth
        }

    def to_json(self):
        return json.dumps(self.to_dict(),default=str)

    def from_json(self):
        json_dict = self.json_obj
        self.handle = json_dict['handle']
        self.name = json_dict['name']
        self.bio = json_dict['bio']
        self.pfp = json_dict['pfp']
        self.followers = json_dict['followers']
        self.following = json_dict['following']
        self.tweets = json_dict['tweets']
        self.likes = json_dict['likes']
        self.retweets = json_dict['retweets']
        self.quotetweets = json_dict['quotetweets']
        self.replies = json_dict['replies']
        self.region = json_dict['region']
        self.creation_date = json_dict['creation_date']
        self.id = json_dict['id']
        self.depth = json_dict.get('depth',0)

    def get_urls(self):
        return [tweet.url for tweet in self.tweets]

    def from_user(self,user):
        #print("Getting user from user object...")
        if type(user) == dict:
            user = user['data']
        else:
            user = user.data
        self.handle = user['username']
        self.name = user['name']
        self.bio = user['description']
        self.pfp = user['profile_image_url']
        self.followers = {"total":user['public_metrics']['followers_count'],"list":[]}
        self.following = {"total":user['public_metrics']['following_count'],"list":[]}
        self.tweets = {"total":user['public_metrics']['tweet_count'],"list":[]}
        self.likes = {"total":0,"list":[]} # If we were using api 1.1 we could get this from the user object
        self.retweets = 0
        self.quotetweets = 0
        self.replies = 0
        self.region = user.get('location',"None")
        self.creation_date = user['created_at']
        self.id = str(user['id'])

    # FIXME: this is a hack, but it works for now
    def from_link(self, api, link):
        # get the user id from the url
        handle = link.split('/')[-1]
        user = api.get_user(username=handle,user_fields='id,username,name,description,profile_image_url,public_metrics,location,created_at')
        self.from_user(user)

    def get_tweets(self, n=10):
        #print(f"get_tweets({n})")
        #try:
        # get top n tweets from user
        # get list of top n tweets from api
        tweets = api.get_users_tweets(self.id, max_results=n, expansions=['author_id'], tweet_fields=['attachments','author_id','public_metrics','text','geo','created_at','in_reply_to_user_id','referenced_tweets','entities'], user_fields=['username','name'])
        ret = []
        #print(tweets)
        #print(tweets[0])
        if tweets.data == None:
            print("ERROR:", tweets)
            self.tweet_type = None
            return
        for i in range(len(tweets[0])):
            #print(type(tweets[0]))
            #print([x['text'] for x in tweets[0]])
            #print([[x for x in tweet] for tweet in tweets[1]['media']])
            tweet = {'data': tweets[0][i],'includes':tweets[1]}
            tweet = Tweet(tweet_obj=tweet, get_attachments=False)
            self.tweets["list"].append(tweet.id)
            ret.append(tweet)
        # self.tweets["list"] = sorted(self.tweets["list"], key=lambda x: x['likes'], reverse=True)
        return ret
        '''
        except Exception as e:
            print("ERROR(get_tweets)\n",e,sep="")
            return []
        '''

    def get_user_lists(self, mode,n=100):
        print(f'get_user_lists({mode},{n})')
        ret = []
        #try:
        if mode == 'followers':
            query_result = api.get_users_followers(self.id, max_results=n, user_fields='id,username,name,description,profile_image_url,public_metrics,location,created_at')
        elif mode == 'following':
            query_result = api.get_users_following(self.id, max_results=n, user_fields='id,username,name,description,profile_image_url,public_metrics,location,created_at')
        elif mode == 'likes':
            query_result = api.get_liked_tweets(self.id, max_results=n, expansions=['author_id'], tweet_fields=['attachments','author_id','public_metrics','text','geo','created_at','in_reply_to_user_id','referenced_tweets','entities'], user_fields=['username','name'])
        else:
            raise(Exception('Invalid follower/following query request'))
        
        # get the user ids, and add them to the relevant list, add user to return list with depth of current depth + 1
        if query_result.data == None:
            return []
        for obj in query_result[0]:
            #print([x for x in query_result[1]['users'][0]])
            #print(obj)
            if mode == 'likes':
                for user in query_result[1]['users']:
                    #print(user,obj)
                    if user['id'] == obj['author_id']:
                        author = user
                        #print(author)
            #print(author)
                obj = {'data':obj, 'includes':{"users":[author]}}
            obj_parse =  User(user_obj=obj,depth=self.depth+1) if mode in ['followers','following'] else Tweet(tweet_obj=obj,get_attachments=False)
            if mode == 'followers':
                self.followers['list'].append(obj_parse.id)
            elif mode == 'following':
                self.following['list'].append(obj_parse.id)
            elif mode == 'favorites':
                self.tweets['list'].append(obj_parse.id)
            ret.append(obj_parse)
            # TODO CHECK IF USER EXISTS ALREADY IN LARGER LIST, OTHERWISE WE WILL GET DUPLICATES IN THE LIST
        
        return ret
        '''except Exception as e:
            print("ERROR\n",e,sep="")
            return []'''


    def __eq__(self,other):
        return self.handle == other.handle and self.bio == other.bio and self.pfp == other.pfp and self.followers == other.followers and self.following == other.following and self.tweets == other.tweets and self.likes == other.likes and self.retweets == other.retweets and self.quotetweets == other.quotetweets and self.replies == other.replies and self.region == other.region

    def __ne__(self,other):
        return not self.__eq__(other)

    def __hash__(self):
        return hash((self.handle, self.bio, self.pfp, self.followers, self.following, self.tweets, self.likes, self.retweets, self.quotetweets, self.replies, self.region))

    def __str__(self):
        return f'{self.name} (@{self.handle})\n({self.pfp})\n{self.bio}\n{self.region}\n{self.creation_date}\n{self.followers} Followers {self.following} Following\nTweets: {self.tweets} Replies: {self.replies}\nLikes: {self.likes} Retweets: {self.retweets} Quotetweets: {self.quotetweets}\n'

    def __repr__(self):
        return f'----------==USER==----------\nid:{self.id}\nName:{self.name}\nHandle:{self.handle}\nBio:{self.bio}\nRegion: {self.region}\n{self.creation_date}\nFollowers: {self.followers}\nFollowing: {self.following}\nTweets: {self.tweets}\nTweets and Replies: {self.replies}\nLikes: {self.likes}\nRetweets: {self.retweets}\nQuotetweets: {self.quotetweets}\n-----------------------------'

    def __lt__(self, other):
        return self.impact() < other.impact()

    def __le__(self, other):
        return self.impact() <= other.impact()

    def __gt__(self, other):
        return self.impact() > other.impact()

    def __ge__(self, other):
        return self.impact() >= other.impact()

class Network(object):
    def __init__(self, users = None, tweets = None, follow_graph = None, like_graph = None, init_user_list = None, get_tweets = False, get_followers = False, get_favorites = False):
        self.users = users
        self.tweets = tweets
        self.follow_graph = follow_graph
        self.like_graph = like_graph
        self.get_tweets = get_tweets
        self.get_followers = get_followers
        self.get_favorites = get_favorites

        if users is None:
            self.users = {}
        if tweets is None:
            self.tweets = {}
        if follow_graph is None:
            self.follow_graph = {}
        if like_graph is None:
            self.like_graph = {}
        if init_user_list != None:
            self.initalize_users(init_user_list)
        
    def populate_followers(self, user_id):
        user = self.users[user_id]
        followers = user.get_user_lists('followers',args.num_followers)
        following = user.get_user_lists('following',args.num_followers)
        for follower in followers:
            if self.follow_graph.get(follower.id,None) == None:
                self.follow_graph[follower.id] = []
            self.follow_graph[follower.id].append(user.id)

            # add the user to the list of users if they are not already in it
            if follower.id not in self.users:
                self.users[follower.id] = follower

        for following in following:
            if self.follow_graph.get(following.id,None) == None:
                self.follow_graph[user.id] = []
            self.follow_graph[user.id].append(following.id)

            if following.id not in self.users:
                self.users[following.id] = following
        
    def populate_likes(self, user_id):
        user = self.users[user_id]
        liked_tweets = user.get_user_lists('likes',args.num_likes)
        for favorite in liked_tweets:
            self.tweets[favorite.id] = favorite
            if self.like_graph.get(favorite.id,None) == None:
                self.like_graph[favorite.id] = []
            self.like_graph[favorite.id].append(user.id)
            user.likes['total'] += 1
            user.likes['list'].append(favorite.id)

    def initalize_users(self, user_list):
        for handle in user_list:
            user = User(url=f"https://twitter.com/{handle}")
            #print(repr(user))
            if user.handle == None:
                print(f"User {handle} not found")
                continue
            if self.get_tweets:
                tweets = user.get_tweets(args.num_tweets)
                for tweet in tweets:
                    self.tweets[tweet.id] = tweet
                    self.like_graph[tweet.id] = []
            self.users[user.id] = user
            assert(user.id in self.users.keys())
            assert(type(user) == User)
            
            self.follow_graph[user.id] = []
            if self.get_followers:
                self.populate_followers(user.id)

            if self.get_favorites:
                self.populate_likes(user.id)

    def __str__(self):
        return f'Network with {len(self.users)} users and {len(self.tweets)} tweets' #TODO Improve
    
    def __repr__(self):
        return f'Network with {len(self.users)} users and {len(self.tweets)} tweets'

    def to_json(self):
        # make json object of network
        network = {"users":{}, "tweets":{}, "follow_graph":{}, "like_graph":{}}
        for user in self.users:
            network["users"][user] = self.users[user].to_dict()
        for tweet in self.tweets:
            network["tweets"][tweet] = self.tweets[tweet].to_dict()
        network["follow_graph"] = self.follow_graph
        network["like_graph"] = self.like_graph
        return network
    
    def from_json(self, j_obj):
        # make network from json object
        self.users = {j_obj['users'][user]['id']:User(json_obj = j_obj['users'][user]) for user in j_obj['users']}
        self.tweets = {j_obj['tweets'][tweet]['id']:Tweet(json_obj=j_obj['tweets'][tweet]) for tweet in j_obj['tweets']}
        self.follow_graph = j_obj['follow_graph']
        self.like_graph = j_obj['like_graph']


    def add_user(self, user):
        self.users[user.id] = user
        for tweet in user.tweets["list"]:
            self.tweets.append(tweet)
        for follower in user.followers["list"]:
            if self.follow_graph.get(follower.id,None) == None:
                self.follow_graph[follower.id] = []
            self.follow_graph[follower.id].append(user.id)
    
    def from_query(self, query):
        tot_tweets = 0
        next_token = None
        while tot_tweets < args.num_tweets:
            #print(f"[{tot_tweets}/{args.num_tweets}]")
            if next_token is None:
                query_result = api.search_recent_tweets(query,max_results=100,expansions=['author_id','attachments.media_keys'], tweet_fields=['attachments','author_id','public_metrics','text','geo','created_at','in_reply_to_user_id','referenced_tweets'], user_fields='id,username,name,description,profile_image_url,public_metrics,location,created_at')
            else:
                query_result = api.search_recent_tweets(query,max_results=100,expansions=['author_id','attachments.media_keys'], tweet_fields=['attachments','author_id','public_metrics','text','geo','created_at','in_reply_to_user_id','referenced_tweets'], user_fields='id,username,name,description,profile_image_url,public_metrics,location,created_at', next_token=next_token)
            next_token = query_result.meta['next_token']
            if query_result.data == None:
                return
            for obj in query_result[0]:
                #print([x for x in query_result[1]['users'][0]])
                #print(obj)
                for user in query_result[1]['users']:
                    #print(user,obj)
                    if user['id'] == obj['author_id']:
                        author = user
                
                tweet_formatted = {'data':obj, 'includes':{'users':[author]}}
                user_formatted = author
                user = User(user_obj=user_formatted,depth=0)
                tweet = Tweet(tweet_obj=tweet_formatted,get_attachments=False)
                if user.id not in self.users:
                    self.users[user.id] = user
                    self.follow_graph[user.id] = []
                self.tweets[tweet.id] = tweet
                user.tweets['list'].append(tweet.id)
            
            print(f"[{len(self.tweets)}/{args.num_tweets}] {len(self.tweets)} tweets, {len(self.users)} users")
            tot_tweets += len(query_result[0])
            if ((tot_tweets // 100) * 100) % 20000 == 0:
                print("SAVING NETWORK")
                json.dump(self.to_json(), open(f"gayboo-{tot_tweets}.json",'w'),default=str)

def parse_args():
    parser = argparse.ArgumentParser(description='Gather tweets and users from Twitter')
    parser.add_argument('-u', '--user', help='user to gather tweets from (Forces User Mode)', required=False, default=None)
    parser.add_argument('-t', '--tweet', help='tweet to gather tweets from (Forces Tweet Mode)', required=False, default=None)
    parser.add_argument('-net', '--network', help='network to gather tweets from (Forces Network Mode)', required=False, default=None, action='store_true')
    parser.add_argument('-o', '--output', help='output file to write to', required=False,default=None)
    parser.add_argument('-nT', '--num_tweets', default=20, help='MAXIMUM number of tweets to gather (30 per request)', required=False, type=int)
    parser.add_argument('-nF', '--num_followers', default=20, help='MAXIMUM number of followers to gather (200 per request)', required=False, type=int)
    parser.add_argument('-nL', '--num_likes', default=20, help='MAXIMUM number of likes to gather (200 per request)', required=False, type=int)
    parser.add_argument('-gT', '--get_tweets', help='Gather tweets', required=False, action='store_true')
    parser.add_argument('-gF', '--get_followers', help='Gather followers', required=False, action='store_true')
    parser.add_argument('-gL', '--get_likes', help='Gather likes', required=False, action='store_true')
    parser.add_argument('-d', '--depth', default=1, help='DEPTH of user to gather (0 = only user, 1 = user and followers/following, 2 = user, followers/following (recurse twice))', required=False)
    parser.add_argument('-b', '--branches', default=100, help='MAXIMUM number of branches to recurse (100)', required=False, type=int)
    parser.add_argument('-c', '--custom', help='runs custom script from the function "custom"', required=False, action='store_true')
    global args
    args = parser.parse_args()

def load_api():
    # load api
    #auth = tweepy.OAuthHandler(os.environ['TWITTER_CONSUMER_KEY'], os.environ['TWITTER_CONSUMER_SECRET'])
    #auth.set_access_token(os.environ['TWITTER_ACCESS_TOKEN_KEY'], os.environ['TWITTER_ACCESS_TOKEN_SECRET'])
    global api

    api = tweepy.Client(bearer_token=os.environ['TWITTER_BEARER_TOKEN'],
                        consumer_key=os.environ['TWITTER_CONSUMER_KEY'],
                        consumer_secret=os.environ['TWITTER_CONSUMER_SECRET'],
                        access_token=os.environ['TWITTER_ACCESS_TOKEN_KEY'],
                        access_token_secret=os.environ['TWITTER_ACCESS_TOKEN_SECRET'],
                        wait_on_rate_limit=True)
    return api

def setup():
    load_dotenv()
    load_api()

# Parses tweet network jsons for tweet text, usernames, handles, and bios
def parse_text_from_networks():
    for n in os.listdir('./data/'):
        if 'network' in n:
            with open(f'./data/{n}', 'r') as f:
                j_obj = json.load(f)
            network = Network()
            network.from_json(j_obj)
        else:
            continue
        tweet_text = []
        # get every tweet text
        for tweet in network.tweets:
            tweet_text.append(network.tweets[tweet].content)
        # get every user name
        user_names = []
        user_handles = []
        user_bios = []
        for user in network.users:
            user_names.append(network.users[user].name)
            user_handles.append(network.users[user].handle)
            user_bios.append(network.users[user].bio)

        # write tweet_text, user_names, user_handles, user_bios to files
        json.dump(tweet_text, open(f'./data/{n.split("-")[1]}/tweet_text.json', 'w'))
        json.dump(user_names, open(f'./data/{n.split("-")[1]}/user_names.json', 'w'))
        json.dump(user_handles, open(f'./data/{n.split("-")[1]}/user_handles.json', 'w'))
        json.dump(user_bios, open(f'./data/{n.split("-")[1]}/user_bios.json', 'w'))

def generate_statistics():
    out = {}
    for n in os.listdir('data/'):
        if 'network' in n:
            group = n.split('-')[1]
            out[group] = {}
            with open(f'data/{n}', 'r') as f:
                j_obj = json.load(f)
            network = Network()
            network.from_json(j_obj)
            print(f'Network {n} loaded')
            out[group]['users'] = len([user for user in network.users.values() if user.depth < 2])
            out[group]['tweets'] = len(network.tweets)
            tweet_totals = [user.tweets['total'] for user in network.users.values() if user.depth < 2]
            follower_totals = [user.followers['total'] for user in network.users.values() if user.depth < 2]
            follower_totals.sort()
            follower_totals_deoutliered = follower_totals[:(len(follower_totals) // 5) * 4]


            following_totals = [user.following['total'] for user in network.users.values() if user.depth < 2]
            following_totals.sort()
            following_totals_deoutliered = following_totals[:(len(following_totals) // 5) * 4]

            ratio_totals = [user.follower_following_ratio() for user in network.users.values() if user.depth < 2]
            ratio_totals.sort()
            ratio_totals_deoutlinered = ratio_totals[:(len(ratio_totals) // 5) * 4]

            out[group]['total_tweets'] = sum(tweet_totals)
            out[group]['avg_tweets'] = sum(tweet_totals) / len(tweet_totals)
            out[group]['max_tweets'] = max(tweet_totals)
            out[group]['total_followers'] = sum(follower_totals)
            out[group]['avg_followers'] = sum(follower_totals) / len(follower_totals)
            out[group]['avg_followers_deout'] = sum(follower_totals_deoutliered) / len(follower_totals_deoutliered)
            out[group]['max_followers'] = max(follower_totals)
            out[group]['total_following'] = sum(following_totals)
            out[group]['avg_following'] = sum(following_totals) / len(following_totals)
            out[group]['avg_following_deout'] = sum(following_totals_deoutliered) / len(following_totals_deoutliered)
            out[group]['max_following'] = max(following_totals)
            out[group]['avg_ratio'] = sum(ratio_totals) / len(ratio_totals)
            out[group]['avg_ratio_deout'] = sum(ratio_totals_deoutlinered) / len(ratio_totals_deoutlinered)
            out[group]['max_ratio'] = max(ratio_totals)
            out[group]['max_ratio_handle'] = [x.handle for x in network.users.values() if x.follower_following_ratio() == max(ratio_totals)][0]
            out[group]['avg_tweet_length'] = sum([len(tweet.content) for tweet in network.tweets.values()]) / len(network.tweets)

            print(f'{len(network.users)} users loaded')
            print(f'{sum(tweet_totals)} tweets have been tweeted by these users')
            print(f'{max(tweet_totals)} tweets have been tweeted by the most active user')
            print(f'{sum(tweet_totals)/len([user for user in network.users.values() if user.depth < 2])} tweets  on average')
            print(f'{len(network.tweets)} tweets loaded in the network currently\n')

    out['totals'] = {}
    out['totals']['users'] = sum([out[group]['users'] for group in out if group != 'totals'])
    out['totals']['tweets'] = sum([out[group]['tweets'] for group in out if group != 'totals'])
    out['totals']['total_tweets'] = sum([out[group]['total_tweets'] for group in out if group != 'totals'])
    out['totals']['avg_tweets'] = sum([out[group]['avg_tweets'] for group in out if group != 'totals']) / 6
    out['totals']['max_tweets'] = max([out[group]['max_tweets'] for group in out if group != 'totals'])
    out['totals']['total_followers'] = sum([out[group]['total_followers'] for group in out if group != 'totals'])
    out['totals']['avg_followers'] = sum([out[group]['avg_followers'] for group in out if group != 'totals']) / 6
    out['totals']['max_followers'] = max([out[group]['max_followers'] for group in out if group != 'totals'])
    out['totals']['total_following'] = sum([out[group]['total_following'] for group in out if group != 'totals'])
    out['totals']['avg_following'] = sum([out[group]['avg_following'] for group in out if group != 'totals']) / 6
    out['totals']['max_following'] = max([out[group]['max_following'] for group in out if group != 'totals'])
    out['totals']['avg_tweet_length'] = sum([out[group]['avg_tweet_length'] for group in out if group != 'totals']) / 6
    
    json.dump(out, open('data/statistics.json', 'w'))

def user_frequency_analysis():
    for n in ['barb','dsmp','joer','kpop','nfts','star']:
        frequencies = json.load(open(f'data/raw-word-freqs/{n}.json'))['keep']
        bio_freqs = json.load(open(f'data/raw-word-freqs/{n}-bio.json'))
        network = Network()
        network.from_json(json.load(open(f'data/network-{n}-current.json')))
        out = {"users": {}, "tweets": {}}
        i = 0
        for user in network.users:
            i += 1
            user_freq_sum = {'absolute': 0, 'normalized': 0, 'orig_only' : 0, 'impact_total': 0}
            bio_freq_sum = {'absolute': 0, 'normalized': 0}
            tweets = network.users[user].tweets['list']
            print(f'[{n} ({i}/{len(network.users)})] {network.users[user].handle} has {len(tweets)} tweets')
            for tweet in tweets:
                tweet = network.tweets[tweet]
                tweet_freq_sum = {'absolute': 0, 'normalized': 0, 'impact': 0}
                for word in tweet.content.split(' '):
                    word = word.strip('.,!?:;').replace("'","").lower()
                    if word in frequencies:
                        if tweet.tweet_type in ['original','replied_to']:
                            user_freq_sum['orig_only'] += frequencies[word] // 10
                        tweet_freq_sum['absolute'] += frequencies[word] // 10
                        user_freq_sum['absolute'] += frequencies[word] // 10
                
                if tweet.tweet_type in ['original','replied_to']:
                    user_freq_sum['impact_total'] += tweet.impact()
                
                out['tweets'][tweet.id] = tweet_freq_sum
                out['users'][user] = user_freq_sum
                out['tweets'][tweet.id]['impact'] = tweet.impact()
                out['tweets'][tweet.id]['handle'] = network.users[user].handle
            for word in network.users[user].bio.split(' '):
                word = word.strip('.,!?:;$#@').replace("'","").lower()
                if word in frequencies:
                  bio_freq_sum['absolute'] += frequencies[word] // 10
            user_freq_sum['impact_avg'] = user_freq_sum['impact_total'] / len(tweets)
            user_freq_sum['absolute_avg'] = user_freq_sum['absolute'] / len(tweets)
            out['users'][user] = {}
            out['users'][user]['value-tweets'] = user_freq_sum
            out['users'][user]['value-bios'] = bio_freq_sum
            out['users'][user]['handle'] = network.users[user].handle
            # sort users by value-tweets
        max_tweet = max([out['users'][user]['value-tweets']['absolute'] for user in out['users']])
        max_bio = max([out['users'][user]['value-bios']['absolute'] for user in out['users']])
        for user in out['users']:
            out['users'][user]['value-tweets']['normalized'] = out['users'][user]['value-tweets']['absolute'] / max_tweet
            out['users'][user]['value-bios']['normalized'] = out['users'][user]['value-bios']['absolute'] / max_bio
        for tweet in out['tweets']:
            out['tweets'][tweet]['normalized'] = out['tweets'][tweet]['absolute'] / max_tweet
        out['users'] = {k: v for k, v in sorted(out['users'].items(), key=lambda item: item[1]['value-tweets']['normalized'], reverse=True)}
        out['tweets'] = {k: v for k, v in sorted(out['tweets'].items(), key=lambda item: item[1]['normalized'], reverse=True)}
        json.dump(out, open(f'analysis_result/freq-result/{n}-freq.json', 'w'))

def add_depth():
    init_users = json.load(open('./data/initial_users.json', 'r'))
    with open(f'./data/network-star-current.json', 'r') as f:
        j_obj = json.load(f)
        network = Network()
        network.from_json(j_obj)
        for user in network.users:
            print(user)
            if network.users[user].handle in init_users['star']:
                network.users[user].depth = 0
            else:
                network.users[user].depth = 1
        json.dump(network.to_json(),open(f'./data/network-star-depth.json','w'),default=str)

def get_d1_tweets():
    for n in ['network-star-current.json']:
        if 'current' in n:
            group = n.split('-')[1]
            with open(f'./data/{n}', 'r') as f:
                j_obj = json.load(f)
                network = Network()
                network.from_json(j_obj)
                print(f'[{group}] loaded')
                userids = list(network.users.keys())
                i = 0
                for user_id in userids:
                    user = network.users[user_id]
                    i += 1
                    if user.depth == 1:
                        print(f'[{group}] {i}/{len(userids)}')
                        print(f"Populating https://twitter.com/{user.handle}")
                        if len(user.tweets['list']) > 0:
                            print(f"Already analyzed https://twitter.com/{user.handle}") 
                        else:
                            #print(f'network.get_followers({user_id})')
                            #network.populate_followers(user_id)
                            tweets = user.get_tweets(n=args.num_tweets)
                            if tweets != None:
                                for tweet in tweets:
                                    network.tweets[tweet.id] = tweet
                                    network.like_graph[tweet.id] = []
                            #network.populate_likes(user_id)
                            # write network to file
                            if i % 25 == 0:
                                json.dump(network.to_json(),open(f'./data/network-{group}-latestsave.json','w'),default=str)
            json.dump(network.to_json(),open(f'./data/network-{group}-expanded.json','w'),default=str)

def gen_filtered_community():
    microcultures = json.load(open('./data/microcultures.json','r'))
    for n in ['barb','dsmp','joer','kpop','nfts','star']:
        f = open(f'./data/network-{n}-current.json', 'r')
        cur_net = Network()
        cur_net.from_json(json.load(f))
        f.close()
        removed_users = 0
        removed_tweets = 0
        orig_users = list(cur_net.users.keys())
        for user in orig_users:
            #print(user)
            if cur_net.users[user].depth == 2:
                continue

            # If the user is in the microculture top 20, include their tweets, else exclude them completely
            top_ids = [x['id'] for x in microcultures[n]['top20']]
            if user not in top_ids:
                removed_users += 1
                
                for tweet in cur_net.users[user].tweets['list']:
                    removed_tweets += 1
                    if tweet in cur_net.tweets:
                        cur_net.tweets.pop(tweet)
                    if (cur_net.like_graph.get(tweet)):
                        cur_net.like_graph.pop(tweet)
                        #print("removed tweet", tweet)
                cur_net.users.pop(user)
                if (cur_net.follow_graph.get(user)):
                    cur_net.follow_graph.pop(user)

        print(f'[{n}] removed {removed_users} users and {removed_tweets} tweets, {len(cur_net.tweets)} tweets / {len(cur_net.users)} users remain')
        json.dump(cur_net.to_json(),open(f'./data/network-{n}-microculture.json','w'),default=str)
                


    # old Generate filtered community, not sure i ever ran it or need it
    '''
        base_path = 'analysis_result/freq-result/'
        for n in ['barb','dsmp','joer','kpop','nfts','star']:
            with open(f'{base_path}{n}-freq.json', 'r') as f:
                j_obj = json.load(f)
                users = j_obj['users']
                tweets = j_obj['tweets']
                out = []
                for user in users[:len(users) // 10]:
                    if users[user]['value-tweets'] > 0:
                        out.append(users[user['id']])
                json.dump(out, open(f'{base_path}{n}-freq-filtered.json', 'w'))
    '''

def plot_user_freq():
    base_path = 'analysis_result/stage2 (full-analysis)/freq-result/'
    for n in ['barb','dsmp','joer','kpop','nfts','star']:
        with open(f'{base_path}{n}-freq.json', 'r') as f:
            j_obj = json.load(f)
            users = j_obj['users']
            # Average filtering
            top_users = {v[0] : v[1] for v in sorted(users.items(), key=lambda k: users[k[0]]['value-tweets']['absolute'], reverse=True)}
            users = top_users
            tweets = j_obj
            out = []
            out_norm = []
            for user in users:
                out.append(users[user]['value-tweets']['absolute'])
                out_norm.append(users[user]['value-tweets']['normalized'])
            # clear the plot
            '''plt.clf()
            plt.title(f'{n.upper()} Absolute User FreqScore Analysis')
            plt.xlabel('User Position')
            plt.ylabel('Absolute Frequency Score')
            plt.plot(out)
            plt.savefig(f'{base_path}{n}-freq-plot-abs.png')
            '''
            #plt.clf()
            plt.plot(out,label=f'{n}')
    plt.title(f'Stage2 Absolute FreqScore Analysis')
    plt.ylabel('Absolute Frequency Score (Tweets)')
    plt.xlabel('User Rank')
    plt.ylim(0,50000)
    plt.legend(['barb','dsmp','joer','kpop','nfts','star'], loc=0, frameon=True)
    plt.savefig(f'{base_path}abs-freq-plot-all-s2.png')
            # save plt to file
            

def get_timeline():
    for n in ['barb','dsmp','joer','kpop','nfts','star']:
        with open(f'./data/network-{n}-current.json', 'r') as f:
            j_obj = json.load(f)
            network = Network()
            network.from_json(j_obj)
            timeline = []
            print("[{}] Populating timeline".format(n))
            for tweet in network.tweets:
                # convert tweet created_at to datetime
                created_at = datetime.strptime(str(network.tweets[tweet].date), "%Y-%m-%d %H:%M:%S%z")
                # convert datetime to epoch time
                epoch_time = int(created_at.timestamp())
                timeline.append(epoch_time)

            json.dump(timeline,open(f'./data/network-{n}-timeline.json','w'),default=str)

def plot_timeline():
    for n in ['barb','dsmp','joer','kpop','nfts','star']:
        with open(f'./data/timeline/network-{n}-timeline.json', 'r') as f:
            timeline = json.load(f)
            mintime = 1650000000
            timeline = [int(x) for x in timeline if x > mintime]
            # clear the plot
            plt.clf()
            # plot timeline as histogram
            plt.hist(timeline, bins=100)
            #plt.plot(timeline)
            # save plt to file
            plt.savefig(f'analysis_result/timelines/timeline-{n}.png')

# attempt to get microcultures from the freq-scores
def get_microcultures():
    out = {}
    for n in ['barb','dsmp','joer','kpop','nfts','star']:
        with open(f'./data/freq-scores/{n}-freq.json', 'r') as f:
            j_obj = json.load(f)
            users = j_obj['users']
            tweets = j_obj['tweets']
            
            # TODO Tweak as needed
            # get the top 20% of users based on absolute score
            top_users = sorted(users, key=lambda k: users[k]['value-tweets']['absolute'], reverse=True)[:len(users) // 5]
            
            # get a list of users that are in the top half of normalized scores (half because quartile would cause dropoff??)
            top_users_norm = [user for user in users if users[user]['value-tweets']['normalized'] > 0.25]

            # get a list of users with an absolute score over 5000
            top_users_abs = [user for user in users if users[user]['value-tweets']['absolute'] > 5000]
            
            # get sorted list of impact scores
            impactful_usrs = sorted(users, key=lambda k: users[k]['value-tweets']['impact'], reverse=True)
            # get a list of users that are in the top half of impact scores
            #print('\n'.join([(users[user]['handle'] +" "+ str(users[user]['value-tweets']['impact'])) for user in impactful_usrs[:20]]))

            out[n] = {}
            out[n]['top20'] = [{'id':user,'value':users[user]['value-tweets']['absolute']} for user in top_users]
            out[n]['normalized'] = [{'id':user,'value':users[user]['value-tweets']['normalized']} for user in top_users_norm]
            out[n]['over5000'] = [{'id':user,'value':users[user]['value-tweets']['absolute']} for user in top_users_abs]

            print(f'[{n}] {len(users)} users, {len(top_users)} top, {len(top_users_norm)} normalized, {len(top_users_abs)} absolute')
            # TODO Handle tweets but for now ignore
            #out[n]['tweets'] = tweets
    json.dump(out,open(f'./data/microcultures.json','w'),default=str)

def plot_keyword_vs_impact():
    legend = []
    for n in ['barb','dsmp','joer','kpop','nfts','star']:
        with open(f'./analysis_result/freq-result/{n}-freq.json', 'r') as f:
            j_obj = json.load(f)
            users = j_obj['users']
            tweets = j_obj['tweets']
            #X_MAX = max([users[u]['value-tweets']['impact_avg'] for u in users])
            X_MAX = 50000
            plot = [(users[user]['value-tweets']['impact_avg'],users[user]['value-tweets']['normalized']) for user in users if users[user]['value-tweets']['impact_avg'] <= X_MAX]
            plot = list(set(plot))
            # clear the plot
            plt.clf()
            plt.xlim(0,max([x[0] for x in plot]))

            x = [v[0] for v in plot]
            y = [v[1] for v in plot]
            plt.scatter(x,y)
            
            #plt.xlim(0,X_MAX)
            # set axes labels
            m, b = np.polyfit(x,y,1)
            print(n,m,b)
            plt.plot([0,X_MAX],[m*x+b for x in [0,X_MAX]])

            legend.append(f'{n} (y={str(m)[:5]}{str(m)[-4:]}x + {str(b)[:5]})')
            plt.title('Average Impact vs Normalized Frequency Value')
            plt.xlabel('Average Impact')
            plt.ylabel('Normalized Frequency Value')
            plt.legend(legend, loc=0, frameon=True)
            legend = []
            plt.savefig(f'./analysis_result/micro_plots/{n}-avg.png')
            #plt.show()

def gen_freq_histogram():
    for n in ['barb','dsmp','joer','kpop','nfts','star']:
        with open(f'./data/freq-scores/{n}-freq.json', 'r') as f:
            j_obj = json.load(f)
            users = j_obj['users']
            plt.clf()
            v = [users[user]['value-tweets']['normalized'] for user in users]
            plt.hist(v,bins=25)
            plt.title(f'{n} normalized freqscores')
            plt.show()

def filter_stage3_freqs():
    for n in ['barb','dsmp','joer','kpop','nfts','star']:
        with open(f'./analysis_result/{n}/word_frequency.json', 'r') as f:
            out = {'keep':{},'removed':{},'s3-missing':{}, 's2-missing':{}}
            j_obj = json.load(f)
            s2_filtered_list = json.load(open(f'./data/stage2/raw-word-freqs/{n}.json','r'))
            print(f'[{n}] {len(j_obj)} keywords')
            for word in j_obj:
                if word in s2_filtered_list['keep']:
                    out['keep'][word] = j_obj[word]
                elif word in s2_filtered_list['removed']:
                    out['removed'][word] = j_obj[word]
                else:
                    out['s3-missing'][word] = j_obj[word]
            for word in s2_filtered_list['keep']:
                if word not in out['keep']:
                    out['s2-missing'][word] = s2_filtered_list['keep'][word]
            print(f'[{n}] {len(out["keep"])} of {len(j_obj)} kept ({len(s2_filtered_list["keep"]) - len(out["keep"])} less than the {len(s2_filtered_list["keep"])} in s2), {len(out["removed"])} removed')
            json.dump(out,open(f'./data/raw-word-freqs/{n}.json','w'))

def custom():
    #network = Network()
    #network.from_query('ranboo')
    #json.dump(network.to_json(),open(f'./data/ranboo-gay.json','w'),default=str)
    #parse_text_from_networks()
    #user_frequency_analysis()
    plot_user_freq()
    #plt.clf()
    #get_timeline()
    #plot_timeline()
    #get_microcultures()
    #plot_keyword_vs_impact()      
    #gen_freq_histogram()  
    #generate_statistics()
    #gen_filtered_community()
    #filter_stage3_freqs()
    
    '''
        TEST CODE TO ENSURE LOADING AND UNLOADING WORKS CORRECTLY
        j_obj = json.loads(open('data/network-dsmp.json', 'r').read())
        network.from_json(j_obj)
        out = network.to_json()
        #print(out['follow_graph'])
        json.dump(out, open('data/network-dsmp-test.json','w'))
        for id in j_obj['follow_graph']:
            if out[id] != j_obj[id]:
                print(f'{out["users"][id]["name"]} is not equal')
        diff = set(j_obj['follow_graph'].values()) - set(out['follow_graph'].values())
        #print(list(j_obj['follow_graph'].keys()), list(out['follow_graph'].keys()))
        print(diff)
    '''
   

def main():
    setup()

    parse_args()
    ret = ...
    if args.custom:
        custom()
        exit()
    if args.user:
        print('==User Mode==')
        ret = User(url=args.user)
        print(repr(ret))
        if args.get_tweets:
            tweets = ret.get_tweets(n=args.num_tweets)
            tweets = {str(tweet.id):tweet.to_dict() for tweet in tweets}
            json.dump(tweets, open(args.output + '.json', 'w'),default=str)
        # get likes from user
        #likes = ret.get_user_lists('likes', n=args.num_likes)
        #likes = {like.id:like.to_dict() for like in likes}
        #print(likes)
        #json.dump(likes, open(args.output + '_likes.json', 'w'),default=str)
        '''following = ret.get_user_lists('following',n=min(args.branches,ret.following['total']))
        followers = ret.get_user_lists('followers',n=min(args.branches,ret.followers['total']))
        # write followers and following to file
        following = {str(user.id):user.to_dict() for user in following}
        followers = {str(user.id):user.to_dict() for user in followers}
        json.dump(following, open(args.output+'_following.json', 'w'),default=str)
        json.dump(followers, open(args.output+'_followers.json', 'w'),default=str)'''
        #print([x.handle for x in ret.following['list']])
        if args.output:
            with open(args.output, 'w') as f:
                f.write(ret.to_json())
    elif args.tweet:
        print(f'Getting Tweet data for {args.tweet}')
        ret = Tweet(url=args.tweet)
        print(repr(ret))
    elif args.network:
        with open("data/initial_users.json", "r") as f:
            handles = json.load(f)['joer']
        print(f'Getting Network data for {handles}')
        network = Network(init_user_list=handles,get_tweets = args.get_tweets, get_followers = args.get_followers, get_favorites = args.get_likes)
        with  open(f"data/network-{args.output.split('.json')[0]}.json", "w") as f:
            f.write(json.dumps(network.to_json(), default=str))


if __name__ == '__main__':
    main()