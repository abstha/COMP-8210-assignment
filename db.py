from pymongo import MongoClient

def get_db(uri="mongodb://localhost:27017", db_name="comp8210"):
    client = MongoClient(uri)
    return client[db_name]