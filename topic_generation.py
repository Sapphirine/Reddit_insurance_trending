import datetime
import praw
from gensim import corpora
from gensim.models.ldamodel import LdaModel
from nltk.corpus import stopwords
from nltk.tokenize import word_tokenize
import openai
from pymongo import MongoClient
import time
import pytz

ny_tz = pytz.timezone('America/New_York')

reddit = praw.Reddit(client_id='ooC7B7QTHMRFkYs1ToW6xw',
                     client_secret='LozZbAV_TZo0hEZG8dXGb_WvMvrpTg',
                     user_agent='6895_app')
subreddits = 'Insurance+Car_Insurance_Help+HealthInsurance+LifeInsurance'

uri = "mongodb+srv://cluster0.ltaxlm0.mongodb.net/?authSource=%24external&authMechanism=MONGODB-X509&retryWrites=true&w=majority"
client = MongoClient(uri,
                     tls=True,
                     tlsCertificateKeyFile='./X509-cert.pem')
db = client['reddit_insurance']
collection = db.topics

stop_words = set(stopwords.words('english'))
stop_words.add('would')
stop_words.add('get')

def preprocess_texts(text):
    tokens = word_tokenize(text)
    tokens = [w.lower() for w in tokens if w.isalpha()]  # Keep only alphabetic tokens, converted to lowercase
    tokens = [w for w in tokens if not w in stop_words]  # Remove stopwords
    return tokens

def safe_request(prompt, model="gpt-3.5-turbo", max_tokens=150):
    try:
        response = openai.ChatCompletion.create(
            model=model,
            messages=[
                {"role": "system", "content": "Please generate a response for the following:"},
                {"role": "user", "content": prompt}
            ],
            max_tokens=max_tokens
        )
        return response.choices[0]['message']['content'].strip()
    except openai.error.RateLimitError as e:
        print("Rate limit exceeded, waiting for 60 seconds...")
        time.sleep(60)
        return safe_request(prompt, model, max_tokens)

documents = []
for submission in reddit.subreddit(subreddits).hot(limit=1000):
    documents.append({
        'text': submission.title + " " + (submission.selftext if submission.selftext else ""),
        'score': submission.score,
        'id': submission.id,
        'title': submission.title,
        'url': submission.url
    })

# Prepare corpus for LDA
texts = [preprocess_texts(document['text']) for document in documents]
dictionary = corpora.Dictionary(texts)
corpus = [dictionary.doc2bow(text) for text in texts]

# LDA analysis
lda = LdaModel(corpus, num_topics=7, id2word=dictionary, passes=15)

# Assuming documents is a list of tuples or dicts that include the text and metadata
# Create a mapping of documents to their primary topics
document_topics = []
for doc_bow in corpus:
    topic_distribution = lda.get_document_topics(doc_bow)
    # Get the topic with the highest probability
    primary_topic = sorted(topic_distribution, key=lambda x: x[1], reverse=True)[0][0]
    document_topics.append(primary_topic)

# Assign documents to topics
topic_documents = {i: [] for i in range(7)}  # Adjust number based on the number of topics
for i, doc_topic in enumerate(document_topics):
    topic_documents[doc_topic].append(documents[i])

created_at = datetime.datetime.now().astimezone(ny_tz).strftime('%Y-%m-%d')
# Process each topic
for i, topic in enumerate(lda.print_topics(num_words=10)):
    prompt_for_title = f"Generate a human-readable title given these keywords from LDA model: {topic}"
    topic_title = safe_request(prompt_for_title, max_tokens=60)

    # Select top posts relevant to the topic for summarization
    hot_posts = []
    sorted_posts = sorted(topic_documents[i], key=lambda x: x['score'], reverse=True)[:5]
    combined_content = "\n\n---\n\n".join([f"Title: {post['title']}\nContent: {post['text']}" for post in sorted_posts])
    # Generate a summary for the combined content
    prompt_for_summary = f"Please generate a concise summary for the following combined posts : {combined_content}"
    combined_summary = safe_request(prompt_for_summary, max_tokens=500)

    for submission in sorted_posts:
        hot_posts.append({
            "post_id": submission['id'],
            "post_title": submission['title'],
            "post_url": submission['url']
        })

    # Store results in MongoDB
    collection.insert_one({
        "topic_id": f"Topic {i+1}",
        "generated_title": topic_title,
        "hot_posts": hot_posts,
        "combined_summary": combined_summary,
        "created_at": created_at
    })