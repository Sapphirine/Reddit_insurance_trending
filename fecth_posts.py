import praw
import datetime
from pymongo import MongoClient

reddit = praw.Reddit(client_id='ooC7B7QTHMRFkYs1ToW6xw',
                     client_secret='LozZbAV_TZo0hEZG8dXGb_WvMvrpTg',
                     user_agent='6895_app')

publisher = pubsub_v1.PublisherClient()
topic_path = publisher.topic_path('empirical-axon-416223', 'postdata')

# Combine subreddits by names separated with '+'
subreddits = 'Insurance+Car_Insurance_Help+HealthInsurance+LifeInsurance'


def fetch_posts():
    start_time = datetime.datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
    end_time = start_time + datetime.timedelta(days=1)

    print(f"Fetching posts for {start_time.date()}")
    for submission in reddit.subreddit(subreddits).new(limit=None):
        submission_time = datetime.datetime.fromtimestamp(submission.created_utc)
        if start_time <= submission_time < end_time:
            # Fetch and store details including comments
            post_data = {
                'title': submission.title,
                'url': submission.url,
                'created_utc': submission.created_utc,
                'num_comments': submission.num_comments,
                'upvotes': submission.score,
                'hotness': submission.hot,
                'comments': []
            }
            # Fetch comments
            submission.comments.replace_more(limit=0)  # Limit to top-level comments only, adjust as needed
            for comment in submission.comments.list():
                post_data['comments'].append({
                    'author': str(comment.author),
                    'body': comment.body,
                    'upvotes': comment.score
                })

            # Store data in MongoDB
            posts_collection.insert_one(post_data)
        elif submission_time < start_time:
            break
