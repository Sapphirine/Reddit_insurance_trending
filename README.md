# How to run the application

Starting the web server is the first step, run the following command:
```
 uvicorn app:app --reload --host 0.0.0.0 --port 8000
```

To start the React front end, go to /frontend/my-app and run the following command:
```
npm start
```
Go to the following URL to see the front end:
```
http://localhost:3000/
```

The topic_geneation.py is the script to generate the topics from the data.
It is hosted as a cronjob and will automatically run at the end of the day.
Users could also run it manually by running the following command:
```
python3 topic_generation.py
```