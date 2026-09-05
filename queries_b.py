from db import get_db
from datetime import datetime
from db import get_db
from datetime import datetime

db = get_db()

week1_start = datetime(2016, 3, 14)
week2_end   = datetime(2016, 3, 28)

count = db.tweets_clean.count_documents({"created_at": {"$gte": week1_start, "$lt": week2_end}})
print("Tweets in the 2-week window:", count)

pipeline = [
    {"$match": {"created_at": {"$gte": week1_start, "$lt": week2_end}}},
    {"$unwind": "$hashtags"},
    {"$addFields": {
        "week_start": {"$dateTrunc": {"date": "$created_at", "unit": "week", "startOfWeek": "monday"}}
    }},
    {"$group": {
        "_id": {"hashtag": "$hashtags", "week_start": "$week_start"},
        "count": {"$sum": 1}
    }},
    {"$sort": {"count": -1}},
    {"$limit": 20}
]
for r in db.tweets_clean.aggregate(pipeline):
    print(r)
    
    
def emerging_hashtags():
    week1_start = datetime(2016, 3, 14)
    week1_end   = datetime(2016, 3, 21)
    week2_start = datetime(2016, 3, 21)
    week2_end   = datetime(2016, 3, 28)

    pipeline = [
        {"$match": {"created_at": {"$gte": week1_start, "$lt": week2_end}}},
        {"$unwind": "$hashtags"},
        {"$addFields": {
            "week_start": {"$dateTrunc": {"date": "$created_at", "unit": "week", "startOfWeek": "monday"}}
        }},
        {"$group": {
            "_id": {"hashtag": "$hashtags", "week_start": "$week_start"},
            "count": {"$sum": 1}
        }},
        {"$group": {
            "_id": "$_id.hashtag",
            "weeks": {"$push": {"week_start": "$_id.week_start", "count": "$count"}}
        }},
        {"$project": {
            "hashtag": "$_id",
            "_id": 0,
            "week1_count": {"$sum": {"$map": {
                "input": {"$filter": {"input": "$weeks", "cond": {"$eq": ["$$this.week_start", week1_start]}}},
                "in": "$$this.count"
            }}},
            "week2_count": {"$sum": {"$map": {
                "input": {"$filter": {"input": "$weeks", "cond": {"$eq": ["$$this.week_start", week2_start]}}},
                "in": "$$this.count"
            }}}
        }},
        {"$match": {"week1_count": {"$gte": 2}, "week2_count": {"$gte": 3}}},  # scaled down from 20/40
        {"$addFields": {"growth_rate": {"$divide": ["$week2_count", "$week1_count"]}}},
        {"$sort": {"growth_rate": -1}},
        {"$limit": 10}
    ]
    return list(db.tweets_clean.aggregate(pipeline))


if __name__ == "__main__":
    for r in emerging_hashtags():
        print(r)