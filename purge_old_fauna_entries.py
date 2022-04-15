import os
from datetime import datetime, timedelta
from faunadb import client, query as q
from tqdm import tqdm
FAUNA_SECRET = os.getenv("FAUNA_SECRET")
if FAUNA_SECRET is None:
    raise ValueError("FAUNA_SECRET environment variable not set")
fClient = client.FaunaClient(FAUNA_SECRET, domain="db.us.fauna.com")
past_date = datetime.strptime("12/02/22", '%d/%m/%y')
current_date = datetime.strptime("09/04/22", '%d/%m/%y')
current_iso_date = current_date.strftime('%Y-%m-%dT%H:%M:%SZ')
past_iso_date = past_date.strftime('%Y-%m-%dT%H:%M:%SZ')
all_docs_ts = fClient.query(q.map_(
    q.lambda_(['ts','ref'], q.get(q.var("ref"))),
    q.paginate(q.range(q.match("ref_by_ts"), [q.to_micros(q.to_time(past_iso_date))], [q.to_micros(q.to_time(current_iso_date))]), size=100000)
))

# delete all old entries
for doc in tqdm(all_docs_ts["data"]):
    # (doc["data"])
    response = fClient.query(q.delete(doc["ref"]))
    # exit(1)
    # fClient.query(q.get(q.ref(doc['ref'])))