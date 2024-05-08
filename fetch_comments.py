import praw
from google.cloud import pubsub_v1
import threading
import json

publisher = pubsub_v1.PublisherClient()
topic_path = publisher.topic_path('empirical-axon-416223', 'comment_data')

reddit = praw.Reddit(client_id='ooC7B7QTHMRFkYs1ToW6xw',
                     client_secret='LozZbAV_TZo0hEZG8dXGb_WvMvrpTg',
                     user_agent='6895_app')

def comment_to_json(comment):
    comment_json = {
        "id": comment.id,
        "name": comment.name,
        "author": comment.author.name if comment.author else "Deleted",
        "body": comment.body,
        "subreddit": comment.subreddit.display_name.lower(),
        "upvotes": comment.ups,
        "downvotes": comment.downs,
        "over_18": comment.over_18,
        "timestamp": comment.created_utc,
        "permalink": comment.permalink,
    }
    return comment_json

def fetch_comments(subreddit_name):
    subreddit = reddit.subreddit(subreddit_name)
    for comment in subreddit.stream.comments(skip_existing=True):
        comment_data = comment_to_json(comment)
        publisher.publish(topic_path, data=json.dumps(comment_data).encode('utf-8'))


if __name__ == "__main__":
    subreddit_list = ['Insurance', 'Car_Insurance_Help', 'HealthInsurance', 'LifeInsurance']
    print("Fetching comments...")

    threads = []

    for subreddit_name in subreddit_list:
        thread = threading.Thread(target=fetch_comments, args=(subreddit_name,))
        threads.append(thread)
        thread.start()

    for thread in threads:
        thread.join()