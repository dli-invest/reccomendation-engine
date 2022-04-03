# grabs recent news from faunadb and determines if it should be recommended and sent to discord
# based on key financial ratios
# iterate through json configuration file with settings to run different jobs.

from typing import List
import pandas as pd
import os
from datetime import datetime, timedelta
from faunadb import client, query as q
# read in csv file with key ratios from https://raw.githubusercontent.com/FriendlyUser/cad_tickers_list/main/static/latest/stocks.csv

# TODO add unit testing when it makes sense
# and we have seen the performance of this function

def get_cheap_stocks(csv_url: str = "https://raw.githubusercontent.com/dli-invest/eod_tickers/main/data/us_stock_data.csv", priceToBook: int = 1, peRatio: int =  3, csv_type: str = "cad_tickers"):
    stock_df = pd.read_csv(csv_url)
    cheapStocks = stock_df[(stock_df["priceToBook"] < priceToBook) & (stock_df["peRatio"] < peRatio)]
    return cheapStocks

def get_row_for_stonk(stock_df: pd.DataFrame, symbol: str = "KGEIF:US", csv_type: str = "cad_tickers"):
    kei_df = stock_df[stock_df["symbol"] == symbol]
    return kei_df

def get_recent_fauna_news(hour_diff = 2)-> List[dict]:
    """
        grab news from fauna db and return a dataframe
    """
    FAUNA_SECRET = os.getenv("FAUNA_SECRET")
    if FAUNA_SECRET is None:
        raise ValueError("FAUNA_SECRET environment variable not set")
    fClient = client.FaunaClient(FAUNA_SECRET, domain="db.us.fauna.com")
    current_date = datetime.now()
    past_date = datetime.now() - timedelta(hours=hour_diff)
    current_iso_date = current_date.strftime('%Y-%m-%dT%H:%M:%SZ')
    past_iso_date = past_date.strftime('%Y-%m-%dT%H:%M:%SZ')
    all_docs_ts = fClient.query(q.map_(
        q.lambda_(['ts','ref'], q.get(q.var("ref"))),
        q.paginate(q.range(q.match("ref_by_ts"), [q.to_micros(q.to_time(past_iso_date))], [q.to_micros(q.to_time(current_iso_date))]), size=1000)
    ))

    return all_docs_ts.get("data", [])

    # [{'data': {'source': 'fin_news_nlp/yahoo_usd_tickers_news', 'url': 'https://ca.finance.yahoo.com/news/why-teck-resources-stock-climbed-204500796.html', 'description': 'Here’s why Teck Resources stock just posted its best quarterly gains in the last five years. The post Why Teck Resources Stock Climbed 44% in Q1 appeared first on The Motley Fool Canada.', 'country': 'USD', 'title': 'The Motley Fool - Why Teck Resources Stock Climbed 44% in Q1', 'company': 'TECH-A.TO', 'unspected': 'fail'}}]


def check_fauna_new_for_reccomendations(cfg: dict):
    """
        For fauna reccomendations I thought that scanning through the news with a recommendation engine would be a good idea, but have decided that going through news for "undervalued" companies is a much better idea and possibly in the future other metrics like small market cap.
    """
    hour_diff = cfg.get("hour_diff", 2)
    fauna_news = get_recent_fauna_news(hour_diff)
    cheap_stonks = get_cheap_stocks()
    # iterate across fauna_news and check if the news is about a cheap stock
    for news in fauna_news:
        # get the company
        company = news.get("data").get("company")

if __name__ == "__main__":
    pass

