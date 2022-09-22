import pandas as pd
import numpy as np
from PIL import Image
import re

from wordcloud import WordCloud, STOPWORDS
import matplotlib.pyplot as plt
import json

import nltk
from nltk.sentiment.vader import SentimentIntensityAnalyzer
from nltk.probability import FreqDist
from nltk.stem import WordNetLemmatizer

nltk.download("stopwords")
nltk.download("punkt")
nltk.download("vader_lexicon")

CUSTOM_FILTER_WORDS = [
    "url",
    "rt",
    "'s",
    "'ll",
    "amp",
    "im",
    "yall",
    "u",
    "ur",
    "m",
    "c",
    "v",
    "ta",
    "x",
    "de",
    "en",
    "ca",
    "la",
    "re",
    "na",
]

DATA_FOLDERS = ["barb", "dsmp", "joer", "kpop", "nfts", "star"]
# DATA_FOLDERS = ["barb"]

# words that have less than cutoff length frequency will not be output to the files
CUTOFF_LENGTH = 0

# with open("data/1000common.txt") as f:
#     common_words = [word.strip() for word in f.readlines()]
#     CUSTOM_FILTER_WORDS = common_words + CUSTOM_FILTER_WORDS
# print(CUSTOM_FILTER_WORDS)


def remove_stopword(text):
    stopword = nltk.corpus.stopwords.words("english")
    text = re.sub(r"http\S+", "url", text)
    text = text.encode("ascii", "ignore").decode()
    wordnet_lemmatizer = WordNetLemmatizer()
    result = [
        wordnet_lemmatizer.lemmatize(word.lower(), pos="v")
        for word in nltk.word_tokenize(text)
    ]
    # print(result)
    a = [
        word
        for word in result
        if word not in stopword
        and word not in CUSTOM_FILTER_WORDS
        and not bool(re.search(r"\d", text))
    ]
    return " ".join(a)


data_analysis_list = []

for data_folder_name in DATA_FOLDERS:
    # read tweets from data/data_folder_name/tweets.txt
    tweets = json.loads(
        open("data/" + data_folder_name + "/user_bios.json", "r").read()
    )

    # Remove stopwords
    tweets = [remove_stopword(tweet) for tweet in tweets]

    # with open("analysis_result/test.json", "w") as outfile:
    #     json.dump(tweets, outfile)

    tweet_blob = " ".join(tweets)
    positive_tweets = []
    neutral_tweets = []
    negative_tweets = []

    tweets_count = len(tweets)
    positive_count = 0
    neutral_count = 0
    negative_count = 0

    sia = SentimentIntensityAnalyzer()

    for tweet in tweets:
        score = sia.polarity_scores(tweet)
        compound_score = score["compound"]

        if compound_score >= 0.05:
            positive_tweets.append(tweet)
            positive_count += 1
        elif compound_score > -0.05:
            neutral_tweets.append(tweet)
            neutral_count += 1
        else:
            negative_tweets.append(tweet)
            negative_count += 1

    blob_scores = sia.polarity_scores(tweet_blob)
    blob_pos = blob_scores["pos"]
    blob_neu = blob_scores["neu"]
    blob_neg = blob_scores["neg"]
    blob_compound = blob_scores["compound"]

    # Plot the sentiment analysis result
    plot1_labels = "Positive", "Neutral", "Negative"
    plot1_sizes = [positive_count, neutral_count, negative_count]
    plot2_labels = "Positive", "Neutral", "Negative"
    plot2_sizes = [blob_pos, blob_neu, blob_neg]

    fig, axs = plt.subplots(2)
    axs[0].pie(plot1_sizes, labels=plot1_labels, autopct="%1.1f%%", startangle=90)
    axs[0].axis("equal")  # Equal aspect ratio ensures that pie is drawn as a circle.
    axs[0].title.set_text("Tweets sentiment categorization")

    axs[1].pie(plot2_sizes, labels=plot2_labels, autopct="%1.1f%%", startangle=90)
    axs[1].axis("equal")  # Equal aspect ratio ensures that pie is drawn as a circle.
    axs[1].title.set_text(
        "Overall sentiment composition.\nCompound score: {0}".format(blob_compound)
    )

    fig.tight_layout()

    plt.savefig(
        "analysis_result/" + data_folder_name + "/bio_sentiment_analysis_result.png"
    )
    plt.close(fig)

    # tweets_df = pd.DataFrame(tweets)
    # tweets_df = tweets_df.drop_duplicates()

    # Wordcloud
    def create_wordcloud(text, filename):
        # mask = np.array(Image.open("cloud.png"))
        stopwords = set(STOPWORDS)
        wc = WordCloud(
            width=1000,
            height=600,
            background_color="white",
            max_words=250,
            stopwords=stopwords,
            repeat=False,
        )
        wc.generate(str(text))
        wc.to_file(filename)

    tweet_blob = tweet_blob.lower()

    tokenizer = nltk.RegexpTokenizer(r"\w+")
    tweet_token = tokenizer.tokenize(tweet_blob)

    # tweet_token = nltk.word_tokenize(tweet_blob)
    filtered_token = [token for token in tweet_token if token not in STOPWORDS]

    pos_blob = " ".join(positive_tweets).lower()
    neu_blob = " ".join(neutral_tweets).lower()
    neg_blob = " ".join(negative_tweets).lower()

    # create_wordcloud(tweet_blob, "analysis_result/" + data_folder_name + "/wc_all.png")
    # create_wordcloud(pos_blob, "analysis_result/" + data_folder_name + "/wc_pos.png")
    # create_wordcloud(neu_blob, "analysis_result/" + data_folder_name + "/wc_neu.png")
    # create_wordcloud(neg_blob, "analysis_result/" + data_folder_name + "/wc_neg.png")

    # print(tweet_blob)
    data_analysis = nltk.FreqDist(filtered_token)

    filter_words = dict(
        [(m, n) for m, n in data_analysis.items() if len(m) > CUTOFF_LENGTH]
    )

    with open(
        "analysis_result/" + data_folder_name + "/bio_word_frequency.json", "w"
    ) as outfile:
        output_words = sorted(filter_words.items(), key=lambda x: x[1], reverse=True)
        json.dump({word[0]: word[1] for word in output_words}, outfile, indent=4)

    data_analysis = nltk.FreqDist(filter_words)

    data_analysis_list.append(data_analysis)

for index in range(len(DATA_FOLDERS)):
    fig = plt.figure(0)
    fig.subplots_adjust(bottom=0.3)
    data_analysis_list[index].plot(40, cumulative=False)

    fig.savefig(
        "analysis_result/" + DATA_FOLDERS[index] + "/bio_frequency_analysis.png"
    )
