import json
import re
from datetime import datetime, timezone
from urllib.parse import urlparse
from pymongo import MongoClient, ASCENDING, UpdateOne


def extract_domain(url: str) -> str:
    if not url:
        return None
    netloc = urlparse(url).netloc
    return netloc.lower().replace("www.", "") if netloc else None

def parse_created_at(posted_time: str) -> datetime:
    return datetime.fromisoformat(posted_time.replace("Z", "+00:00"))

def strip_urls_mentions(text: str) -> str:
    no_urls = re.sub(r"https?://t\.co/\S+", "", text)
    no_mentions = re.sub(r"@\w+", "", no_urls)
    return no_mentions.strip()

def parse_tweet(raw: dict) -> dict:
    created_at = parse_created_at(raw["object"]["postedTime"])  # <-- changed from raw["postedTime"]
    entities = raw.get("twitter_entities", {})
    hashtags = [h["text"].lower() for h in entities.get("hashtags", [])]
    mentions = [m["screen_name"] for m in entities.get("user_mentions", [])]
    urls = [
        {"expanded_url": u.get("expanded_url"), "domain": extract_domain(u.get("expanded_url"))}
        for u in entities.get("urls", [])
    ]
    return {
        "id_str": str(raw["id"]),
        "user_id": str(raw["actor"]["id"]),
        "created_at": created_at,
        "text": raw.get("text", ""),
        "clean_text": strip_urls_mentions(raw.get("text", "")),
        "hashtags": hashtags,
        "mentions": mentions,
        "urls": urls,
        "hour_of_day": created_at.hour,
        "weekday": created_at.strftime("%A"),
        "has_link": len(urls) > 0,
        "lang_guess": raw.get("twitter_lang", "und"),
    }

def parse_user(raw: dict) -> dict:
    actor = raw["actor"]
    links = actor.get("links") or []
    profile_url = links[0]["href"] if links else None
    return {
        "user_id": str(actor["id"]),
        "screen_name": actor.get("preferredUsername"),
        "name": actor.get("displayName"),
        "location": (actor.get("location") or {}).get("displayName"),
        "url_domain": extract_domain(profile_url) if profile_url else None,
    }


def load_raw(path: str) -> list[dict]:
    with open(path) as f:
        first_char = f.read(1)
        f.seek(0)
        if first_char == "[":
            return json.load(f)
        else:
            return [json.loads(line) for line in f if line.strip()]


def run_pipeline(path: str, mongo_uri: str = "mongodb://localhost:27017", db_name: str = "comp8210"):
    client = MongoClient(mongo_uri)
    db = client[db_name]

    raw_records = load_raw(path)
    print(f"Loaded {len(raw_records)} raw records")

    tweets = []
    users = {}  
    skipped = 0

    for raw in raw_records:
        try:
            tweets.append(parse_tweet(raw))
            u = parse_user(raw)
            users[u["user_id"]] = u  
        except (KeyError, TypeError) as e:
            skipped += 1
            continue  # malformed record, skip rather than crash whole pipeline

    print(f"Parsed {len(tweets)} tweets, {skipped} skipped due to missing fields")

    latest_by_id = {}
    for t in tweets:
        existing = latest_by_id.get(t["id_str"])
        if existing is None or t["created_at"] > existing["created_at"]:
            latest_by_id[t["id_str"]] = t

    deduped_tweets = list(latest_by_id.values())
    print(f"After dedup: {len(deduped_tweets)} unique tweets "
          f"({len(tweets) - len(deduped_tweets)} duplicates removed)")
    if raw_records:
        db.tweets_raw.delete_many({})
        db.tweets_raw.insert_many(raw_records)

    db.tweets_clean.delete_many({})
    db.tweets_clean.insert_many(deduped_tweets)

    user_ops = [
        UpdateOne({"user_id": u["user_id"]}, {"$set": u}, upsert=True)
        for u in users.values()
    ]
    if user_ops:
        db.users.bulk_write(user_ops)

    print(f"Wrote {len(deduped_tweets)} tweets to tweets_clean, "
          f"{len(users)} users upserted")

    db.tweets_clean.create_index([("created_at", ASCENDING)])
    db.tweets_clean.create_index([("hashtags", ASCENDING), ("created_at", ASCENDING)])
    db.tweets_clean.create_index([("user_id", ASCENDING), ("created_at", ASCENDING)])
    db.tweets_clean.create_index([("urls.domain", ASCENDING), ("created_at", ASCENDING)])

    db.users.create_index([("user_id", ASCENDING)], unique=True)
    db.users.create_index([("screen_name", ASCENDING)])

    print("Indexes created.")
    client.close()


if __name__ == "__main__":
    run_pipeline("./10000_tweets_clean.json/10000_tweets_clean.json")