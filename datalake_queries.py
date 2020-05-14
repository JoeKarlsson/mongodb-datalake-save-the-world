import sys
from datetime import timedelta

from pymongo import MongoClient

if len(sys.argv) != 3:
    print('You forgot the MongoDB URIs for Data Lake and Atlas!')
    print(' - python3 datalake_queries.py "URI Data Lake" "URI Atlas Cluster"')
    print(' - python3 datalake_queries.py "mongodb://user:pwd@datalake-abcde.dublin-irl.a.query.mongodb.net/test?ssl=true&authSource=admin" '
          '"mongodb+srv://user:pwd@bigcluster.abcde.mongodb.net/test?retryWrites=true&w=majority"')
    exit(1)

mongo_data_lake = MongoClient(host=(sys.argv[1]), socketTimeoutMS=10000, connectTimeoutMS=10000, serverSelectionTimeoutMS=10000)
db_data_lake = mongo_data_lake.get_database("world")
iot_data_lake = db_data_lake.get_collection("iot")
cold = db_data_lake.get_collection("cold_iot")

mongo_atlas = MongoClient(host=(sys.argv[2]), socketTimeoutMS=10000, connectTimeoutMS=10000, serverSelectionTimeoutMS=10000)
db_atlas = mongo_atlas.get_database("world")
iot_atlas = db_atlas.get_collection("iot")

pipeline = [
    {'$sort': {'date': 1}},
    {'$group': {'_id': '$device', 'count': {'$sum': 1}, 'first_date': {'$first': '$date'}, 'last_date': {'$last': '$date'}}}
]

print('In the cold_iot collection from Data Lake, I only have access to the archived data.')
docs = cold.aggregate(pipeline)
for doc in docs:
    print(doc)

print('\nIn the iot collection from Atlas, I only have access to the hot data in Atlas.')
docs = iot_atlas.aggregate(pipeline)
for doc in docs:
    print(doc)

print('\nIn the iot collection from Data Lake, I have access to the archived data AND the hot data in MongoDB Atlas.')
docs = iot_data_lake.aggregate(pipeline)
for doc in docs:
    print(doc)

print('\nUsing the Data Lake connection, I can also write documents to S3.')
date_start = iot_atlas.find().sort("date", 1).limit(1).next()['date']
date_stop = date_start + timedelta(days=1)
print('Dates', date_start, '=>', date_stop)
query = {'date': {'$gte': date_start, '$lt': date_stop}}
pipeline_s3 = [
    {'$match': query},
    {
        '$out': {
            's3': {
                'bucket': 'cold-data-mongodb',
                'region': 'eu-west-1',
                'filename': date_start.isoformat('T', 'milliseconds') + 'Z-' + date_stop.isoformat('T', 'milliseconds') + 'Z',
                'format': {'name': 'json', 'maxFileSize': "200MiB"}
            }
        }
    }
]
iot_data_lake.aggregate(pipeline_s3)

print('\nNow I can remove my docs from my hot Atlas cluster.')
print('=>', iot_atlas.delete_many(query).deleted_count, 'have been removed from the hot Atlas Cluster.')

print('\nLet\'s check that all the documents can still be accessed by Data Lake in the iot collection.')
docs = iot_data_lake.aggregate(pipeline)
for doc in docs:
    print(doc)

mongo_atlas.close()
mongo_data_lake.close()
