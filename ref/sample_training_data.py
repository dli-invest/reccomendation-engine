import pandas as pd 
import json 
import spacy
from spacytextblob.spacytextblob import SpacyTextBlob
# read data_full.json into dataframe    
df = pd.read_json("data_full.json")
# drop duplicates

# make new df with only columns we need, text, description, source, a bunch of senitment analysis columns

# save new df to csv
# title is text 


nlp = spacy.load("en_core_web_sm")
nlp.add_pipe("spacytextblob")

df["text"] = df["title"]
# delete title column
# add column to dataframe for sentiment analysis from spacy
df["title_polarity"] = df["title"].apply(lambda x: nlp(x)._.polarity)
df["desc_polarity"] = df["description"].apply(lambda x: nlp(x)._.polarity)
df["title_subjectivity"] = df["title"].apply(lambda x: nlp(x)._.subjectivity)
df["desc_subjectivity"] = df["description"].apply(lambda x: nlp(x)._.subjectivity)

# delete title column 
del df["title"]

# iterate across each row in df

# make target column for extremely positive and negative articles
# if title_polarity > 0.5 or desc_polarity > 0.5:
#     df["target"] = "positive"
df["target"] = df.apply(lambda x: "positive" if x["title_polarity"] > 0.6 or x["desc_polarity"] > 0.6 else "negative", axis=1)

# manually adjust the rest

df.to_csv("training_data.csv", index=False)