# Data Collection Architecture of Sensor Fault Detection using Confluent Kafka and MongoDB

[Apache Kafka](https://kafka.apache.org) is an open-source distributed event streaming platform used by thousands of companies for high-performance data pipelines, streaming analytics, data integration, and mission-critical applications. Kafka handles a boundless stream of data that sequentially writes events into commit logs, allowing real-time data movement between our services. Also, [MongoDB](https://www.mongodb.com) is the world's most popular modern database for handling massive volumes of heterogeneous data. Together MongoDB and Kafka make up the heart of many modern data architectures.

Integrating Kafka with external systems like MongoDB is done using [Kafka Connect](https://docs.confluent.io/platform/current/connect/index.html). This API enables users to leverage ready-to-use components that stream data from external systems into Kafka topics and from Kafka topics into external systems.

[![MongoDB and Kafka](https://webassets.mongodb.com/_com_assets/cms/kafka-mongodb-diagram-faymcnggw8.png)](https://www.mongodb.com/blog/post/getting-started-with-the-mongodb-connector-for-apache-kafka-and-mongodb-atlas)

### Getting Started with Confluent Kafka.

The steps are as follows:

- [**1. Confluent Account Setup**](docs/ConfluentAccountSetup.md)
- [**2. Kafka Cluster Setup**](docs/ConfluentClusterSetup.md)
- [**3. Create Kafka Topic**](docs/ConfluentTopicCreation.md)
- [**4. Obtain Cloud API Secrets**](docs/KeysandSecrets.md)
- [**5. Obtain Schema API Secrets**](docs/SchemaRegistry.md)

#### To use Confluent Kafka, we need the following details from the Confluent Dashboard.
```
=========================================================================
Paste the following credentials as system environment variables.
=========================================================================

ENDPOINT_SCHEMA_URL = https://psrc-znpo0.ap-southeast-2.aws.confluent.cloud
API_KEY = vUVUOKW4N6N44WLWA
API_SECRET_KEY = nNfJRIsJ/9ddodtaRgwOwwue9Qnb8Y0R1YFMkxbJy/V5vmhKGP3QLaIUCmjZwYi6
BOOTSTRAP_SERVER = pkc-41p56.asia-south1.gcp.confluent.cloud:9092
SECURITY_PROTOCOL = SASL_SSL
SSL_MACHENISM = PLAIN
SCHEMA_REGISTRY_API_KEY = W7FNHUXG54KRMF4L
SCHEMA_REGISTRY_API_SECRET = qOOM4EiHpVCI1vlZpXv7XWY0CQVbln2j7uN37l1w1zBrlgq8wEjoKi3pRt8wfchH
```

### Getting Started with MongoDB (Atlas and Compass).

The steps are as follows:

- Signup for [MongoDB Atlas](https://www.mongodb.com).
- Create a database and its corresponding collection name.
- Obtain the MongoDB Connection String from Atlas.
- Download and Install [MongoDB Compass](https://www.mongodb.com/try/download/compass) on your Desktop.
- Connect MongoDB with any applications using the MongoDB Connection String URL.

#### To use MongoDB, we need the "MongoDB Connection String URL" from MongoDB Atlas.
```
=========================================================================
Paste the following credentials as system environment variables.
=========================================================================

MONGO_DB_URL = mongodb+srv://root:<password>@sensordb.8eqgr7f.mongodb.net/?retryWrites=true&w=majority
```
