from google.cloud import pubsub_v1
import json
import nltk
from nltk.sentiment import SentimentIntensityAnalyzer
from pymongo import MongoClient
import numpy as np
from nrclex import NRCLex

# Initialize Pub/Sub subscriber client
subscriber = pubsub_v1.SubscriberClient()
subscription_path = subscriber.subscription_path('empirical-axon-416223', 'comment_data-sub')

nltk.download('vader_lexicon', quiet=True)
analyzer = SentimentIntensityAnalyzer()

uri = "mongodb+srv://cluster0.ltaxlm0.mongodb.net/?authSource=%24external&authMechanism=MONGODB-X509&retryWrites=true&w=majority"
client = MongoClient(uri,
                     tls=True,
                     tlsCertificateKeyFile='./X509-cert.pem')
db = client['reddit_insurance']
collection = db.comments

def analyze_sentiment(text):

    sentences = nltk.sent_tokenize(text)
    compound_scores = []

    for sentence in sentences:
        sentiment = analyzer.polarity_scores(sentence)
        compound_scores.append(sentiment['compound'])

    if compound_scores:
        avg_compound_score = np.mean(compound_scores)
    else:
        avg_compound_score = 0

    return {"sentiment_score": avg_compound_score}

def analyze_emotion_nrc(text):
    emotions_sum = {'anger': 0, 'anticip': 0, 'disgust': 0, 'fear': 0, 'joy': 0, 'negative': 0, 'positive': 0,
                    'sadness': 0, 'surprise': 0, 'trust': 0}

    emotion = NRCLex(text).affect_frequencies

    for key in emotions_sum.keys():
        if key in emotion:
            emotions_sum[key] = emotion[key]

    return emotions_sum

def callback(message):
    comment = json.loads(message.data.decode('utf-8'))

    sentiment_score = analyze_sentiment(comment['body'])
    emotion_scores = analyze_emotion_nrc(comment['body'])

    comment.update(sentiment_score)
    comment.update(emotion_scores)

    collection.insert_one(comment)

    # Acknowledge the message
    message.ack()

# Subscribe to the topic
subscriber.subscribe(subscription_path, callback=callback)
print(f"Listening for messages on {subscription_path}...\n")

# Keep the main thread running to listen to messages indefinitely
import time
try:
    while True:
        time.sleep(10)
except KeyboardInterrupt:
    print("Exiting...")
