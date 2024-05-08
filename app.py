import logging
from fastapi import FastAPI, Query, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from pymongo import MongoClient, ASCENDING, DESCENDING
import certifi
from datetime import datetime, timedelta
from typing import List, Optional
import pytz

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
ny_tz = pytz.timezone('America/New_York')

app = FastAPI()

origins = [
    "http://localhost:3000",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

uri = "mongodb+srv://cluster0.ltaxlm0.mongodb.net/?authSource=%24external&authMechanism=MONGODB-X509&retryWrites=true&w=majority"

def serialize_document(document):
    # Convert ObjectId fields to string
    document['_id'] = str(document['_id'])
    return document

class Post(BaseModel):
    post_id: str
    post_title: str
    post_url: str

class Topic(BaseModel):
    topic_id: str
    generated_title: str
    hot_posts: List[Post]
    created_at: str
    combined_summary: str


@app.on_event("startup")
async def startup_db_client():
    app.client = MongoClient(uri,
                         tls=True,
                         tlsCertificateKeyFile='./X509-cert.pem',
                         tlsCAFile=certifi.where())
    app.db = app.client['reddit_insurance']
    app.comments_collection = app.db.comments
    app.topics_collection = app.db.topics


@app.on_event("shutdown")
async def shutdown_db_client():
    # Close the MongoDB connection when the app shuts down
    app.client.close()

@app.get("/")
async def root():
    return {"message": "Hello World"}


@app.get("/comments")
def read_comments(sort_by: str = Query(..., alias="sort_by"),
                        time_range: str = Query(..., alias="time_range"),
                        keyword: str = Query(None, alias="keyword"),
                        offset: int = 0, limit: int = 10):

    valid_sort_columns = ["sentiment_score", "joy", "sadness", "anger", "surprise", "fear", "disgust", "anticip",
                          "trust"]

    if sort_by not in valid_sort_columns:
        raise HTTPException(status_code=400, detail="Invalid sort_by value")

    end_date = datetime.utcnow().astimezone(ny_tz)
    start_date = end_date

    if time_range == "today":
        start_date -= timedelta(days=1)
    elif time_range == "this_week":
        start_date -= timedelta(weeks=1)
    elif time_range == "this_month":
        start_date -= timedelta(days=30)  # Approximation for month
    elif time_range == "this_year":
        start_date -= timedelta(days=365)  # Approximation for year
    else:
        raise HTTPException(status_code=400, detail="Invalid time_range value")

    query = {'timestamp': {'$gte': start_date.timestamp(), '$lte': end_date.timestamp()}}

    if keyword:
        query['body'] = {'$regex': keyword, '$options': 'i'}  # Case-insensitive search

    comments_cursor = app.comments_collection.find(query).sort(sort_by, -1).skip(offset).limit(limit)
    comments = list(comments_cursor)

    comments_dict_list = [
        {"author_name": comment["author"], "content": comment["body"], "upvotes": comment.get("upvotes", 0),
         "downvotes": comment.get("downvotes", 0), "permalink": comment["permalink"],
         "sentiment_score": comment["sentiment_score"], "anger": comment["anger"],
         "anticipation": comment["anticip"], "disgust": comment["disgust"], "fear": comment["fear"], "joy": comment["joy"],
         "sadness": comment["sadness"], "surprise": comment["surprise"], "trust": comment["trust"]}
        for comment in comments
    ]

    return {"comments": comments_dict_list}


@app.get("/topics/", response_model=List[Topic])
def read_topics(date: Optional[str] = Query(None), limit: Optional[int] = 7):
    try:
        # Query topics by created_at date
        query = {}
        if date:
            query["created_at"] = date
        topics_cursor = app.topics_collection.find(query).sort([
            ("created_at", DESCENDING),
            ("topic_id", ASCENDING)
        ]).limit(limit)
        topics_list = list(topics_cursor)
        # Serialize each document for JSON response
        return [serialize_document(topic) for topic in topics_list]
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

