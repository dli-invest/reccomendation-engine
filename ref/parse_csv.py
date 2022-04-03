import os
from faunadb import client, query as q
import pandas as pd
import spacy
from spacytextblob.spacytextblob import SpacyTextBlob
FAUNA_SECRET = os.getenv("FAUNA_SECRET")
fClient = client.FaunaClient(FAUNA_SECRET, domain="db.us.fauna.com")
documents = fClient.query(
  q.map_(
    q.lambda_("x", q.get(q.var("x"))),
    q.paginate(q.documents(q.collection("Article")), size=1000000),
  )
)

fauna_data = documents["data"]
# get data property from each document in fauna_data
formatted_data = [doc["data"] for doc in fauna_data]

# if raw_data.csv exists, append to it
if os.path.exists("raw_data.csv"):
    df = pd.read_csv("raw_data.csv")
    df = pd.concat([df, pd.DataFrame.from_records(formatted_data)], ignore_index=True)
    # drop duplicates
    df.drop_duplicates(subset=['url'], inplace=True)
    df.to_csv("raw_data.csv", index=False)
else: 
    df = pd.DataFrame.from_records(formatted_data)
    df.to_csv("raw_data.csv", index=False)

# apply csv logic and get training data for ai model

# spacy load small model
nlp = spacy.load("en_core_web_sm")
nlp.add_pipe("spacytextblob")

# add column to dataframe for sentiment analysis from spacy
df["title_polarity"] = df["title"].apply(lambda x: nlp(x)._.polarity)
df["desc_polarity"] = df["description"].apply(lambda x: nlp(x)._.polarity)
df["title_subjectivity"] = df["title"].apply(lambda x: nlp(x)._.subjectivity)
df["desc_subjectivity"] = df["description"].apply(lambda x: nlp(x)._.subjectivity)
df.to_csv("training_data.csv", index=False)
