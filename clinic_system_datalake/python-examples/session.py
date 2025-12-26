from pyspark.sql import SparkSession

spark_master = "local[*]"

hdfs_base_uri = "hdfs://namenode:8020"

hive_meta_uri = "thrift://localhost:9083"

spark = SparkSession.builder \
    .appName("hudi_example_fhir_etl") \
    .master(spark_master) \
    .config("spark.jars.packages", "org.apache.hudi:hudi-spark3.5-bundle_2.12:1.0.2") \
    .config("spark.sql.hive.convertMetastoreParquet", 'false') \
    .config("spark.serializer", "org.apache.spark.serializer.KryoSerializer") \
    .config("spark.sql.catalog.spark_catalog", "org.apache.spark.sql.hudi.catalog.HoodieCatalog") \
    .config("spark.sql.extensions", "org.apache.spark.sql.hudi.HoodieSparkSessionExtension") \
    .config("spark.sql.legacy.timeParserPolicy", "LEGACY") \
    .getOrCreate()
