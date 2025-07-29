import pg8000
import pandas as pd
from pyspark.sql import SparkSession
from awsglue.context import GlueContext
from awsglue.dynamicframe import DynamicFrame

# Initialize Spark & Glue Context
spark = SparkSession.builder.appName("PostgresWithPg8000").getOrCreate()
glueContext = GlueContext(spark.sparkContext)

def run_query_with_pg8000(host, port, dbname, user, password, query):
    try:
        # Step 1: Connect to PostgreSQL
        conn = pg8000.connect(
            host=host,
            port=int(port),
            database=dbname,
            user=user,
            password=password,
            ssl_context=None  # If SSL not required; else configure appropriately
        )

        # Step 2: Run query and fetch result into pandas DataFrame
        cursor = conn.cursor()
        cursor.execute(query)
        columns = [desc[0] for desc in cursor.description]
        rows = cursor.fetchall()
        pandas_df = pd.DataFrame(rows, columns=columns)

        cursor.close()
        conn.close()

        # Step 3: Convert to Spark DataFrame
        spark_df = spark.createDataFrame(pandas_df)

        # Step 4: Optional — Convert to Glue DynamicFrame
        dynamic_frame = DynamicFrame.fromDF(spark_df, glueContext, "aurora_df")

        return dynamic_frame

    except Exception as e:
        print(f"❌ ERROR in pg8000 query: {e}")
        raise
