exports = async function(){
  const s3 = context.services.get('AWS').s3("eu-west-1");
  const iot = context.services.get("mongodb-atlas").db("world").collection("iot");

  const first_date = (await iot.find().sort({"date": 1}).limit(1).next()).date;
  const next_day = new Date(first_date);
  next_day.setDate(next_day.getDate() + 1);
  console.log("Archiving from: " + first_date);
  console.log("Archiving to  : " + next_day);
  const query = {"date": {"$gte": first_date, "$lt": next_day}};

  const docs = await iot.find(query).sort({"date": 1}).toArray();

  console.log("Sending " + docs.length + " docs to S3.");
  const s3res = await s3.PutObject({
    "Bucket": "cold-data-mongodb",
    "Key": first_date.toISOString() + "-" + next_day.toISOString() + ".1.json",
    "Body": EJSON.stringify(docs)
  });

  console.log("S3 ETag: " + s3res.ETag);

  return iot.deleteMany(query);
};
