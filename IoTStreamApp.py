import time
import json
from kafka import KafkaProducer
from datetime import datetime

from pyspark.sql import SparkSession
from pyspark.sql.functions import from_json, col, expr, to_timestamp, window
from pyspark.sql.types import StructType, StructField, StringType, DoubleType

kafka_topic_name = "device-data"
kafka_bootstrap_servers = 'localhost:9092'

# Set chính sách thời gian mặc định
spark = SparkSession \
    .builder \
    .appName("Streaming Demo") \
    .master("local[4]") \
    .config("spark.jars.packages", "org.apache.spark:spark-sql-kafka-0-10_2.12:3.5.0") \
    .getOrCreate()

spark.conf.set("spark.sql.legacy.timeParserPolicy", "LEGACY")

schema = StructType([
    StructField("date", StringType(), True),
    StructField("humidity", StringType(), True),  # Đổi kiểu dữ liệu thành StringType
    StructField("temperature", StringType(), True),  # Đổi kiểu dữ liệu thành StringType
    StructField("time", StringType(), True),
])

iot = (spark.readStream
       .format("kafka")
       .option("kafka.bootstrap.servers", kafka_bootstrap_servers)
       .option("subscribe", kafka_topic_name)
       .option("startingOffsets", "earliest")
       .load())

my_df = iot.selectExpr("CAST(value AS STRING) as json")

parsed_df = my_df.select(from_json(col("json").cast("string"), schema).alias("IOT")).select("IOT.*")

# Định dạng lại thời gian
parsed_df = parsed_df.withColumn("timestamp", to_timestamp(expr("CONCAT(date, ' ', time)"), "MM/dd/yy HH:mm:ss"))

parsed_df.printSchema()

result_df = (parsed_df
             .withWatermark("timestamp", "1 minutes")
             .groupBy(window("timestamp", "1 minutes"))
             .agg(
                 expr("coalesce(avg(cast(temperature as double)), 0) as avg_temperature"),
                 expr("coalesce(avg(cast(humidity as double)), 0) as avg_humidity")
             )
             .select("window.start", "window.end", "avg_temperature", "avg_humidity"))

query = (result_df.writeStream
         .outputMode("update")
         .format("console")
         .option("truncate", "false")
         .start())

query.awaitTermination()