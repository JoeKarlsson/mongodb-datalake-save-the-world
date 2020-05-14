exports = function(){
  const iot = context.services.get("mongodb-atlas").db("world").collection("iot");
  iot.find().sort({"date": 1}).limit(1).next()
  .then( doc => {
    const first_date = doc.date;
    const next_day = new Date(first_date);
    next_day.setDate(next_day.getDate() + 1);
    console.log("Archiving from: " + first_date);
    console.log("Archiving to  : " + next_day);
    const query = {"date": {"$gte": first_date, "$lt": next_day}};
    iot.find(query).sort({"date": 1}).toArray()
    .then( docs => {
      console.log("Sending " + docs.length + " docs to S3.");
      const s3 = context.services.get('AWS').s3("eu-west-1");
      s3.PutObject({
        "Bucket": "cold-data-mongodb",
        "Key": first_date.toISOString() + "-" + next_day.toISOString() + ".1.json",
        "Body": EJSON.stringify(docs)
      })
      .then(result => {
        console.log("S3 ETag: " + result.ETag);
        iot.deleteMany(query).then(result => {
          console.log(EJSON.stringify(result));
          return result;
        });
      });
    });
  });
};