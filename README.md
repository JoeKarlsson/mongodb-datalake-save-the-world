# Save The World And Money With MongoDB Data Lake

This repository stores the code for my MongoDB.live 2020 talk.

## IOT Dataset

I used [this repository](https://github.com/MaBeuLux88/IoT-generator-mongodb) to generate the IOT dataset.

Here is a sample document.

```javascript
{
	"_id" : ObjectId("5ebc936378eac4871e4325e1"),
	"device" : "PTA101",
	"date" : ISODate("2020-01-03T00:00:00Z"),
	"unit" : "°C",
	"avg" : 19.35,
	"max" : 27.5,
	"min" : 13,
	"missed_measures" : 1,
	"recorded_measures" : 59,
	"measures" : [
		{
			"minute" : 0,
			"value" : 19
		},
		{
			"minute" : 1,
			"value" : 20.5
		},
		{
			"minute" : 2,
			"value" : 18
		},
		...
	]
}
```

## Realm Function

The Realm Function in the file [realm_retire_function.js](realm_retire_function.js) does the following things: 

1) finds the date of the oldest sensor entry,
2) finds all the documents in the MongoDB Atlas cluster (hot) between this date and the next day,
3) sends these docs to an AWS S3 bucket,
4) remove these docs from the hot cluster.

Note: The name of the file in the S3 bucket looks like this `2020-01-01T00:00:00.000Z-2020-01-02T00:00:00.000Z.1.json`. This is important because this allows me to [identify ranges of queryable data from the filename](https://docs.mongodb.com/datalake/reference/examples/path-syntax-examples#identify-ranges-of-queryable-data-from-filename) and speed up my queries in Data Lake.

## Data Lake Config

In this configuration, you will see: 

- Two data stores: 
  - One is the S3 data source,
  - Ths other is the MongoDB Atlas data source.
  
- One database definition with 2 collections:
  - cold_iot: it contains only the S3 bucket data.
  - iot: it contains the data from both data sources.

```json
{
  "databases": [
    {
      "name": "world",
      "collections": [
        {
          "name": "cold_iot",
          "dataSources": [
            {
              "path": "/{min(date) isodate}-{max(date) isodate}.1.json",
              "storeName": "cold-data-mongodb"
            }
          ]
        },
        {
          "name": "iot",
          "dataSources": [
            {
              "path": "/{min(date) isodate}-{max(date) isodate}.1.json",
              "storeName": "cold-data-mongodb"
            },
            {
              "collection": "iot",
              "database": "world",
              "storeName": "BigCluster"
            }
          ]
        }
      ],
      "views": []
    }
  ],
  "stores": [
    {
      "provider": "s3",
      "bucket": "cold-data-mongodb",
      "delimiter": "/",
      "includeTags": false,
      "name": "cold-data-mongodb",
      "region": "eu-west-1"
    },
    {
      "provider": "atlas",
      "clusterName": "BigCluster",
      "name": "BigCluster",
      "projectId": "5e78e83fc61ce37535921257"
    }
  ]
}
```

## Archive with Python

The script [datalake_queries.py](datalake_queries.py) has access to both MongoDB Data Lake and the hot Atlas Cluster.

Using the Data Lake connection, I can use the **Federated Queries** to access the entire dataset (archived and hot) and with `$out` I can retire data to S3.

```shell script
python3 datalake_queries.py "URI Data Lake" "URI Atlas Cluster"
```
