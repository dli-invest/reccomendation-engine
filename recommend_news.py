# grabs recent news from faunadb and determines if it should be recommended and sent to discord
# based on key financial ratios
# iterate through json configuration file with settings to run different jobs.

from typing import List
import pandas as pd
import os
import json
import time
import requests
from datetime import datetime, timedelta
from faunadb import client, query as q
# read in csv file with key ratios from https://raw.githubusercontent.com/FriendlyUser/cad_tickers_list/main/static/latest/stocks.csv

# TODO add unit testing when it makes sense
# and we have seen the performance of this function
# https://raw.githubusercontent.com/dli-invest/eod_tickers/main/data/us_stock_data.csv
def get_cheap_stocks(csv_url: str = "https://raw.githubusercontent.com/FriendlyUser/cad_tickers_list/main/static/latest/stocks.csv", priceToBook: int = 1, peRatio: int =  3, csv_type: str = "cad_tickers"):
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


def ex_to_yahoo_ex(row: pd.Series) -> str:
    """
    Parameters:
        ticker: ticker from pandas dataframe from cad_tickers
        exchange: what exchange the ticker is for
    Returns:
    """
    ticker = str(row["symbol"])
    exchange = row["exShortName"]
    if exchange == "CSE":
        # strip :CNX from symbol
        ticker = ticker.replace(":CNX", "")
    # Missing a exchange code
    if exchange in ["OTCPK", "NYSE", "NASDAQ", "NYE", "NCM", "NSM", "NGS"]:
        ticker = ticker.replace(":US", "")
    ticker = ticker.replace(":US", "")
    # 1min, 5min, 15min, 30min, 60min, daily, weekly, monthly
    switcher = {"TSXV": "V", "TSX": "TO", "CSE": "CN"}
    yahoo_ex = switcher.get(exchange, None)
    if yahoo_ex is not None:
        return f"{ticker}.{yahoo_ex}"
    return ticker

def post_webhook_content(url, data: dict):
    try:
        result = requests.post(
            url, data=json.dumps(data), headers={"Content-Type": "application/json"}
        )
        result.raise_for_status()
    except requests.exceptions.HTTPError as err:
        print(err)
        status_code = err.response.status_code
        if status_code == 429:
            print("Rate limited by discord")
            # wait for a minute
            time.sleep(60)
            post_webhook_content(url, data)
    else:
        print("Payload delivered successfully, code {}.".format(result.status_code))

def yahoo_ex_remove(yahoo_ex: str) -> str:
    """
        convert yahoo exchange to exchange code
    """
    # 1min, 5min, 15min, 30min, 60min, daily, weekly, monthly
    # split content before and after the .
    # for canadian stonks
    # check if yahoo_ex has .
    if yahoo_ex is None:
        return yahoo_ex
    if "." in yahoo_ex:
        [ticker, ex] = yahoo_ex.split(".")

        if ex in ["TO", "CSE", "V", "CN", "TSX", "TSXV"]:
            return ticker
    return yahoo_ex


def map_article_to_embed(fauna_item: dict, fields: List[dict] = [])-> dict:
    """
    Take an article and map the embed to the article
    """
    article = fauna_item.get("data", {})
    embed = {
        "title": article["title"],
        "url": article["url"],
        "description": article["description"],
        "username": article["source"],
    }
    fauna_timestamp = fauna_item.get("ts", "")
    if fauna_timestamp != "":
        unix_timestamp = fauna_timestamp / 1000 / 1000
        timestamp = datetime.fromtimestamp(unix_timestamp)
        # YYYY-MM-DDTHH:MM:SS.MSSZ
        embed["timestamp"] = timestamp.strftime("%Y-%m-%dT%H:%M:%SZ")


    if "company" in article:
        embed["author"] = {
            "name": article["company"]
        }

    if len(fields) > 0:
        embed["fields"] = fields
    return embed

def check_fauna_new_for_reccomendations(cfg: dict):
    """
        For fauna reccomendations I thought that scanning through the news with a recommendation engine would be a good idea, but have decided that going through news for "undervalued" companies is a much better idea and possibly in the future other metrics like small market cap.
    """
    discord_url = os.getenv("DISCORD_WEBHOOK")
    hour_diff = cfg.get("hour_diff", 2)
    fauna_news = get_recent_fauna_news(hour_diff)
    subset_stock_df = get_cheap_stocks()
    # iterate across fauna_news and check if the news is about a cheap stock
    embeds = []
    for item in fauna_news:
        # get the company
        company = item.get("data").get("company")
        if company is None:
            continue
        ticker = yahoo_ex_remove(company)
        row = get_row_for_stonk(subset_stock_df, ticker)
        if row.empty:
            continue
        fields = [{
            "name": "priceToBook",
            "value": str(row["priceToBook"].iloc[0]),
            "inline": True
        }, {
            "name": "peRatio",
            "value": str(row["peRatio"].iloc[0]),
            "inline": True
        }]
        embed = map_article_to_embed(item, fields)
        embeds.append(embed)
        if len(embeds) >= 6:
            data = {
                "embeds": embeds
            }
            post_webhook_content(discord_url,  data)
            embeds = []
        # adjust company name to match the csv file
    if len(embeds) >= 1:
        data = {
            "embeds": embeds
        }
        post_webhook_content(discord_url,  data)
        embeds = []

if __name__ == "__main__":
    check_fauna_new_for_reccomendations({
        "hour_diff": 2
    })

