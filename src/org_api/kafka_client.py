from aiokafka import AIOKafkaProducer
from ichec_logger import get_logger


logger = get_logger()

async def init_kafka(config, app):
    producer = AIOKafkaProducer(
        bootstrap_servers=config["kafka"]["bootstrap_servers"]
    )
    await producer.start()
    app.state.kafka_producer = producer
    logger.info("[Kafka] Producer started")

async def shutdown_kafka(app):
    producer = getattr(app.state, "kafka_producer", None)
    if producer:
        await producer.stop()
        logger.info("[Kafka] Producer stopped")

async def send_kafka_message(app, message: str, topic: str = None):
    config = app.state.config
    if not config["kafka"].get("enabled"):
        logger.info("[Kafka] Disabled in config.")
        return

    producer = getattr(app.state, "kafka_producer", None)
    if producer:
        topic = topic or config["kafka"]["topic"]
        await producer.send_and_wait(topic, message.encode("utf-8"))
        logger.info(f"[Kafka] Sent message to topic: {topic}")
