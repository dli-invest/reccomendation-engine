# grabs recent news from faunadb and determines if it should be recommended and sent to discord
# based on key financial ratios
# iterate through json configuration file with settings to run different jobs.

import pandas as pd
import os
from datetime import datetime, timedelta
from faunadb import client, query as q
# read in csv file with key ratios from https://raw.githubusercontent.com/FriendlyUser/cad_tickers_list/main/static/latest/stocks.csv

stock_df = pd.read_csv("https://raw.githubusercontent.com/dli-invest/eod_tickers/main/data/us_stock_data.csv")

# get ticker with symbol kei.to
kei_df = stock_df[stock_df["symbol"] == "KGEIF:US"]

print(kei_df)

print(kei_df["priceToBook"])
print(kei_df["peRatio"])

# priceToBook below 1 in kei_df
cheapStocks = stock_df[(stock_df["priceToBook"] < 1) & (stock_df["peRatio"] < 3)]

def get_recent_news(hour_diff = 2):

    FAUNA_SECRET = os.getenv("FAUNA_SECRET")
    fClient = client.FaunaClient(FAUNA_SECRET, domain="db.us.fauna.com")
    current_date = datetime.now()
    past_date = datetime.now() - timedelta(hours=hour_diff)
    current_iso_date = current_date.strftime('%Y-%m-%dT%H:%M:%SZ')
    past_iso_date = past_date.strftime('%Y-%m-%dT%H:%M:%SZ')
    all_docs_ts = fClient.query(q.map_(
        q.lambda_(['ts','ref'], q.get(q.var("ref"))),
        q.paginate(q.range(q.match("ref_by_ts"), [q.to_micros(q.to_time(past_iso_date))], [q.to_micros(q.to_time(current_iso_date))]), size=1000)
    ))

    print(all_docs_ts)
    print(len(all_docs_ts.get("data")))

    # [{'data': {'source': 'fin_news_nlp/yahoo_usd_tickers_news', 'url': 'https://ca.finance.yahoo.com/news/why-teck-resources-stock-climbed-204500796.html', 'description': 'Here’s why Teck Resources stock just posted its best quarterly gains in the last five years. The post Why Teck Resources Stock Climbed 44% in Q1 appeared first on The Motley Fool Canada.', 'country': 'USD', 'title': 'The Motley Fool - Why Teck Resources Stock Climbed 44% in Q1', 'company': 'TECH-A.TO', 'unspected': 'fail'}}]