StayScope UI upgrade
====================

Included in app.py:
1. Property Explorer cards with sorting, budget pick, top-rated pick, pagination, full table and CSV download.
2. Interactive India map using listing latitude/longitude.
3. Filter-aware market insights and existing charts/KPI cards.
4. Big Data pipeline panel with HDFS/MapReduce CLI checks, Spark result-file checks, architecture summary, and optional Cassandra connection check.

Preserved:
- Existing local username/password authentication (PBKDF2 hashes in stayscope_users.db)
- Airbnb red/white theme
- Existing sidebar filters, charting, 3D plot, analytics CSV downloads

Install required packages in the project's active virtual environment:
  python -m pip install -r requirements_stayscope.txt

Back up your current app.py, then replace it with this updated app.py in the same project folder as airbnb_cleaned.csv.
Run from the Ubuntu/WSL project terminal:
  source ~/spark-env/bin/activate
  python -m streamlit run app.py --server.fileWatcherType poll

Notes:
- Keep airbnb_cleaned.csv next to app.py.
- HDFS and MapReduce status is checked through the hdfs CLI available to the environment running Streamlit.
- Spark is currently verified by the presence of result files in spark_results/; the app does not launch a Spark job on every rerun.
- Cassandra is not falsely marked connected. To enable its connection test, install cassandra-driver and set CASSANDRA_HOST to the reachable Cassandra host. This connection test does not itself create tables or persist listings.
- The map needs an internet connection to load OpenStreetMap tiles.
