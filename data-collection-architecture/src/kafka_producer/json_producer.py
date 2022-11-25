from uuid import uuid4
from src.kafka_config import sasl_conf, schema_config
from src.kafka_logger import logging
from src.entity.generic import Generic, instance_to_dict
from confluent_kafka import Producer
from confluent_kafka.serialization import (
    StringSerializer,
    SerializationContext,
    MessageField,
)
from confluent_kafka.schema_registry import SchemaRegistryClient
from confluent_kafka.schema_registry.json_schema import JSONSerializer


def delivery_report(err, msg):
    """Logging the success or failure of message delivery."""
    if err is not None:
        logging.info(f"Delivery failed for User record {msg.key()}: {err}")
        return
    logging.info(
        f"User record {msg.key()} successfully produced to {msg.topic()} [{msg.partition()}] at offset {msg.offset()}"
    )


def product_data_using_file(topic, file_path):
    schema_str = Generic.get_schema_to_produce_consume_data(file_path=file_path)
    schema_registry_conf = schema_config()
    schema_registry_client = SchemaRegistryClient(schema_registry_conf)

    string_serializer = StringSerializer("utf_8")
    json_serializer = JSONSerializer(
        schema_str, schema_registry_client, instance_to_dict
    )

    producer = Producer(sasl_conf())

    print(f"Producing user records to topic {topic}. ^C to exit.")

    producer.poll(0.0)

    try:
        for instance in Generic.get_object(file_path=file_path):
            print(instance)
            producer.produce(
                topic=topic,
                key=string_serializer(str(uuid4()), instance.to_dict()),
                value=json_serializer(
                    instance, SerializationContext(topic, MessageField.VALUE)
                ),
                on_delivery=delivery_report,
            )
    except KeyboardInterrupt:
        pass
    except ValueError:
        print("Invalid input, discarding records.....")

    print("\nFlushing records.....")
    producer.flush()
