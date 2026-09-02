import pandas as pd
import json

with open("./10000_tweets_clean.json/10000_tweets_clean.json") as f:
    data = json.load(f)
print(json.dumps(data[0], indent=2, default=str)[:3000])

load = pd.read_json("./10000_tweets_clean.json/10000_tweets_clean.json")

load = pd.json_normalize(load.to_dict(orient='records'))

print (load)

print (load.columns.tolist())