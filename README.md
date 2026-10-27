# Airbnb Big Data Analytics

## 1. Project Overview
This project analyzes Airbnb property listings using Hadoop HDFS, Hadoop MapReduce, Apache Spark, and Apache Cassandra.

## 2. Dataset
- Original dataset: `final_data.csv`
- Cleaned dataset: `airbnb_cleaned.csv`
- Preprocessing script: `inspect_data.py`
- Dataset fields include property name, location, state, country, coordinates, room type, guest capacity, price, and stars.

## 3. Hadoop HDFS
**Purpose:** Store the dataset in Hadoop Distributed File System.

**Verification command:**
```bash
hdfs dfs -ls /airbnb
```

Dataset location:
`/airbnb/input/airbnb_cleaned.csv`

## 4. Hadoop MapReduce
**Purpose:** Count the frequency of words in property names.

Implementation: `WordCount.java`

Compiled artifact: `wordcount.jar`

Input:
`/airbnb/wordcount/input/property_names.txt`

Output:
`/airbnb/wordcount/output/part-r-00000`

Verification command:
```bash
hdfs dfs -cat /airbnb/wordcount/output/part-r-00000
```

## 5. Apache Spark
**Purpose:** Perform distributed-style data analysis using Spark DataFrames.

Implementation: `spark_analytics.py`

Analyses:
- Average price and property count by state
- Property count by room type
- Ten most expensive properties
- Average price by guest capacity

Run command:
```bash
python spark_analytics.py
```

Output folder: `spark_results/`

### Spark Output Files

Spark generated the following output directories:

- `spark_results/price_by_state/` — average price and property count grouped by state.
- `spark_results/room_type_counts/` — property count grouped by room type.

Each output directory contains a CSV part file and Spark success metadata.

**Verification command:**
```bash
find spark_results -name 'part-*.csv'
```

**Sample observations:**
- Entire villa: 220 records.
- Farm stay: 58 records.
- Punjab: average listed price 12,327 across 3 records.

These observations describe the current dataset and should be rechecked if the input data changes.

## 6. Apache Cassandra
**Status:** Pending implementation and verification.

Planned use: Store selected Airbnb analytics results in Cassandra and demonstrate database queries.

## 7. Evidence
Store screenshots of successful commands, code, and outputs in the `evidence/` folder.

## 8. Notes
Record the actual execution date, dataset row count, errors encountered, and final results after verifying them. Do not claim an incomplete component as implemented.


python -m streamlit run app.py --server.fileWatcherType poll


cd /mnt/c/Users/Shruti/OneDrive/Desktop/BDAL/Airbnb-Big-Data-Analytics


 cat app.py