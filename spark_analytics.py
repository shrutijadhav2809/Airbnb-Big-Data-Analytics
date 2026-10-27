
from pyspark.sql import SparkSession
from pyspark.sql.functions import col, avg, count, round, desc

# Start Spark
spark = (
    SparkSession.builder
    .appName("Airbnb Big Data Analytics")
    .master("local[*]")
    .getOrCreate()
)

spark.sparkContext.setLogLevel("ERROR")

# Load cleaned Airbnb dataset
file_path = "airbnb_cleaned.csv"
df = spark.read.csv(file_path, header=True, inferSchema=True)

print("\n========== DATASET OVERVIEW ==========")
print("Total rows:", df.count())
print("Total columns:", len(df.columns))
df.printSchema()

print("\n========== SAMPLE RECORDS ==========")
df.show(5, truncate=False)

print("\n========== AVERAGE PRICE BY STATE ==========")
df.groupBy("state").agg(
    round(avg(col("price")), 2).alias("average_price"),
    count("*").alias("property_count")
).orderBy(desc("average_price")).show(truncate=False)

print("\n========== PROPERTY COUNT BY ROOM TYPE ==========")
df.groupBy("roomType").agg(
    count("*").alias("property_count")
).orderBy(desc("property_count")).show(truncate=False)

print("\n========== TOP 10 MOST EXPENSIVE PROPERTIES ==========")
df.select("name", "location", "state", "price", "roomType") \
    .orderBy(desc("price")) \
    .show(10, truncate=False)

print("\n========== AVERAGE PRICE BY GUEST CAPACITY ==========")
df.groupBy("numberOfGuests").agg(
    round(avg(col("price")), 2).alias("average_price"),
    count("*").alias("property_count")
).orderBy("numberOfGuests").show(truncate=False)


# Save analytics results to CSV files
import os

output_dir = "spark_results"
os.makedirs(output_dir, exist_ok=True)

# 1. Average price and property count by state
df.groupBy("state").agg(
    round(avg("price"), 2).alias("average_price"),
    count("*").alias("property_count")
).orderBy(desc("average_price")) \
 .coalesce(1) \
 .write.mode("overwrite").option("header", True) \
 .csv(f"{output_dir}/price_by_state")

# 2. Property count by room type
df.groupBy("roomType").agg(
    count("*").alias("property_count")
).orderBy(desc("property_count")) \
 .coalesce(1) \
 .write.mode("overwrite").option("header", True) \
 .csv(f"{output_dir}/room_type_counts")

print("Analytics CSV files saved in the spark_results folder.")


spark.stop()
print("\nSpark analytics completed successfully!")
