import pandas as pd
import json
from pymongo import MongoClient
from datetime import datetime, timedelta



client = MongoClient("mongodb://localhost:27017")
db = client["comp8210"]

earliest = db.tweets_clean.find_one(sort=[("created_at", 1)])
latest = db.tweets_clean.find_one(sort=[("created_at", -1)])
print("Earliest:", earliest["created_at"])
print("Latest:", latest["created_at"])

latest_dt = datetime(2016, 4, 1, 2, 4, 6)

# Find the Monday of the week containing 'latest_dt'
days_since_monday = latest_dt.weekday()  # Monday=0, Sunday=6
this_week_monday = latest_dt - timedelta(days=days_since_monday)
this_week_monday = this_week_monday.replace(hour=0, minute=0, second=0, microsecond=0)

# Since latest_dt is mid-week (not Sunday 23:59), this current week is PARTIAL -> exclude it
# So week2 = the last FULL week = the week before this_week_monday
week2_start = this_week_monday - timedelta(days=7)
week2_end = this_week_monday  # exclusive upper bound

week1_start = week2_start - timedelta(days=7)
week1_end = week2_start

print("Week1:", week1_start, "to", week1_end)
print("Week2:", week2_start, "to", week2_end)

# with open("./10000_tweets_clean.json/10000_tweets_clean.json") as f:
#     data = json.load(f)
# print(json.dumps(data[0], indent=2, default=str)[:3000])

# load = pd.read_json("./10000_tweets_clean.json/10000_tweets_clean.json")

# load = pd.json_normalize(load.to_dict(orient='records'))

# print (load)

# print (load.columns.tolist()) 