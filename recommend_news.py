# grabs recent news from faunadb and determines if it should be recommended and sent to discord
# based on key financial ratios
# iterate through json configuration file with settings to run different jobs.

from typing import List
import pandas as pd
import os
import json
import time
import requests
from spacytextblob.spacytextblob import SpacyTextBlob
import dateparser
import spacy
import re
import math
from tqdm import tqdm
from datetime import datetime, timedelta
from faunadb import client, query as q
# read in csv file with key ratios from https://raw.githubusercontent.com/FriendlyUser/cad_tickers_list/main/static/latest/stocks.csv

# TODO add unit testing when it makes sense
# and we have seen the performance of this function
# https://raw.githubusercontent.com/dli-invest/eod_tickers/main/data/us_stock_data.csv
def get_cheap_stocks(csv_url: str = "https://raw.githubusercontent.com/FriendlyUser/cad_tickers_list/main/static/latest/stocks.csv", priceToBook: int = 2, peRatio: int =  2, csv_type: str = "cad_tickers"):
    stock_df = pd.read_csv(csv_url)
    cheap_stonks = stock_df[(stock_df["priceToBook"] < priceToBook) & (stock_df["peRatio"] < peRatio)]
    cheap_stonks = cheap_stonks[(cheap_stonks["priceToBook"] > 0) & (cheap_stonks["peRatio"] > 0)]
    return cheap_stonks

# get stonks with low market cap
def get_penny_stonks(csv_url: str = "https://raw.githubusercontent.com/FriendlyUser/cad_tickers_list/main/static/latest/stocks.csv", csv_type: str = "cad_tickers"):
    stock_df = pd.read_csv(csv_url)
    low_mc_df = stock_df[stock_df["MarketCap"] < 50E7]
    return low_mc_df

def millify(n):
    millnames = ['',' Thousand',' Million',' Billion',' Trillion']
    n = float(n)
    millidx = max(0,min(len(millnames)-1,
                        int(math.floor(0 if n == 0 else math.log10(abs(n))/3))))

    return '{:.0f}{}'.format(n / 10**(3 * millidx), millnames[millidx])

def get_row_for_stonk(stock_df: pd.DataFrame, symbol: str = "KGEIF:US", csv_type: str = "cad_tickers"):
    df_row = stock_df[stock_df["symbol"] == symbol]
    return df_row

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
        try:
            [ticker, ex] = yahoo_ex.split(".")
        except Exception as e:
            ticker = yahoo_ex.split(".")[0]
            ex = yahoo_ex.split(".")[-1]

        # CNX stonks treated differently
        if ex in ["CSE", "CN"]:
            return f"{ticker}:CNX"

        # for webmoney should be no extension
        if ex in ["TO", "V", "TSX", "TSXV"]:
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

def check_fauna_new_for_reccomendations(cfg: dict, fauna_news: List[dict] = []):
    """
        For fauna reccomendations I thought that scanning through the news with a recommendation engine would be a good idea, but have decided that going through news for "undervalued" companies is a much better idea and possibly in the future other metrics like small market cap.
    """
    discord_url = os.getenv("DISCORD_WEBHOOK")
    hour_diff = cfg.get("hour_diff", 2)
    if len(fauna_news) == 0:
        fauna_news = get_recent_fauna_news(hour_diff)
    subset_stock_df = get_cheap_stocks()
    small_cap_stonks = get_penny_stonks()
    # combine subset_stonk_df with small_cap_stonks and remove duplicates
    subset_stonks = subset_stock_df.append(small_cap_stonks).drop_duplicates(subset=["symbol"])
    # iterate across fauna_news and check if the news is about a cheap stock
    embeds = []

    clean_fauna_news = []
    # remove fauna news containing Zacks or Motley
    for fauna_item in fauna_news:
        article = fauna_item.get("data", {})
        if "Motley" in article["title"] or "Zacks" in article["title"]:
            continue
        clean_fauna_news.append(fauna_item)
    
    # remove fauna_news that matches string
    for item in tqdm(clean_fauna_news):
        # get the company
        company = item.get("data").get("company")
        if company is None:
            continue
        ticker = yahoo_ex_remove(company)
        row = get_row_for_stonk(subset_stonks, ticker)
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
        }, {
            "name": "marketCap",
            "value": millify(row["MarketCap"].iloc[0]),
            "inline": True
        }, {
            "name": "industry",
            "value": str(row["industry"].iloc[0]),
            "inline": True
        }]
        embed = map_article_to_embed(item, fields)
        embeds.append(embed)
        if len(embeds) >= 6:
            data = {
                "username": "reccomendation-engine/alerts",
                "embeds": embeds
            }
            post_webhook_content(discord_url,  data)
            embeds = []
        # adjust company name to match the csv file
    if len(embeds) >= 1:
        data = {
            "username": "reccomendation-engine/alerts",
            "embeds": embeds
        }
        post_webhook_content(discord_url,  data)
        embeds = []



def check_for_earnings(items: List[dict]):
    nlp = spacy.load("en_core_web_sm")
    nlp.add_pipe("spacytextblob")
    subset_stock_df = get_cheap_stocks()
    embeds_to_sent = []
    for item in tqdm(items):
        doc = nlp(item["data"]["title"])
        extracted_date = None
        extracted_title = item["data"]["title"]
        multiword_list  = ["next week's", "simply wall", "three years", "zacks", "virtual investor conference", "motley fool", "roadshow series", "institutional investors conference", "speak at"]
            # check if extracted_title has any substrings in multiword list
        pattern = re.compile(r'\b(?:' + '|'.join(re.escape(s) for s in multiword_list) + r')\b')
        matches = pattern.findall(extracted_title.lower())
        if len(matches) > 0:
            continue
        for ent in doc.ents:
            # ignore "dates" if they can be parsed as a number
            if ent.label_ == "DATE":
                try:
                    if ent.text.lower() in ["today", "tomorrow", "yesterday", "decade", "40-year", "friday", "thursday", "wednesday", "tuesday", "monday", "sunday", "saturday", "january", "February", "march", "april", "may", "june", "july", "august", "september", "october", "november", "december", "last year", "next week's", "week", "-", "zacks", "roadshow", "participate", "convention"]:
                        continue
                    # check ent.text in multiword list contains
                    num = int(ent.text, 10)

                except ValueError as e:
                    # print(e)
                    # dont want the number to be parsed as a date
                    extracted_date = dateparser.parse(ent.text)
                    if extracted_date != None:
                        if extracted_date.strftime('%Y-%m-%d') == datetime.now().strftime('%Y-%m-%d'):
                            extracted_date = None
                            continue
                        break

        if extracted_date != None:
            # append to list of files to be sent
            company = item.get("data").get("company")
            if company is None:
                continue
            ticker = yahoo_ex_remove(company)
            row = get_row_for_stonk(subset_stock_df, ticker)
            if row.empty:
                continue
            # may want different fields here
            fields = [{
                "name": "priceToBook",
                "value": str(row["priceToBook"].iloc[0]),
                "inline": True
            }, {
                "name": "peRatio",
                "value": str(row["peRatio"].iloc[0]),
                "inline": True
            }, {
                "name": "marketCap",
                "value": millify(row["MarketCap"].iloc[0]),
                "inline": True
            },  {
            "name": "industry",
            "value": str(row["industry"].iloc[0]),
            "inline": True
        }]
            embed = map_article_to_embed(item, fields)
            embeds_to_sent.append(embed)
            extracted_date = None
            # send to discord
            if len(embeds_to_sent) >= 6:
                data = {
                    "username": "reccomendation-engine/earnings",
                    "embeds": embeds_to_sent
                }
                discord_url = os.getenv("DISCORD_WEBHOOK")
                post_webhook_content(discord_url,  data)
                embeds_to_sent = []
            continue
    if len(embeds_to_sent) > 0:
        data = {
            "username": "reccomendation-engine/earnings",
            "embeds": embeds_to_sent
        }
        discord_url = os.getenv("DISCORD_WEBHOOK")
        post_webhook_content(discord_url,  data)
        embeds_to_sent = [] 

if __name__ == "__main__":
    unseen_fauna_news = []
    unseen_urls = []
    # open urls.txt if it exists
    if os.path.isfile("data/urls.txt"):
        with open("data/urls.txt", "r", encoding="utf-8") as f:
            urls = f.readlines()
            # strip newlines from urls
            urls = [url.strip() for url in urls]
    else:
        urls = []
    # fetch all news in the last weak
    fauna_news = get_recent_fauna_news(1*60*7)
    # append list of all urls in fauna news to a file called urls.txt
    for item in fauna_news:
        url = item["data"]["url"]
        if url not in urls:
            urls.append(url)
            unseen_urls.append(url)
            unseen_fauna_news.append(item)
    with open("data/urls.txt", "a", encoding="utf-8") as f:
        for url in unseen_urls:
            if url is None or url != "":
                f.write(url + "\n")

    check_fauna_new_for_reccomendations({
        "hour_diff": 2
    }, unseen_fauna_news)

    # check for earnings
    check_for_earnings(unseen_fauna_news)
