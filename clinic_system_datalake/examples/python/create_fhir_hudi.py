from pyspark.sql import SparkSession
import json

# 初始化 Spark Session with Hudi
spark = SparkSession.builder \
    .appName("FHIR-Hudi-Write") \
    .config("spark.jars.packages", "org.apache.hudi:hudi-spark3.5-bundle_2.12:1.0.2") \
    .config("spark.serializer", "org.apache.spark.serializer.KryoSerializer") \
    .config("spark.sql.extensions", "org.apache.spark.sql.hudi.HoodieSparkSessionExtension") \
    .config("spark.sql.catalog.spark_catalog", "org.apache.spark.sql.hudi.catalog.HoodieCatalog") \
    .config("spark.sql.hive.convertMetastoreParquet", "false") \
    .config("spark.sql.legacy.timeParserPolicy", "LEGACY") \
    .getOrCreate()

# 讀取扁平化的 FHIR 資料
#with open('fhir_flattened_for_hudi.json', 'r') as f:
#    fhir_data = json.load(f)
with open('/opt/spark-apps/fhir_flattened_for_hudi.json', 'r') as f:
    fhir_data = json.load(f)

# 按照資源類型分組並寫入不同的 Hudi table
resource_types = {}
for record in fhir_data:
    rtype = record['resourceType']
    if rtype not in resource_types:
        resource_types[rtype] = []
    resource_types[rtype].append(record)

print(f"Found {len(resource_types)} resource types to process...")

# 為每種資源類型建立 Hudi table
for resource_type, records in resource_types.items():
    print(f"\nProcessing {resource_type}: {len(records)} records")

    # 創建 DataFrame
    df = spark.createDataFrame(records)

    # 顯示 schema
    print(f"Schema for {resource_type}:")
    df.printSchema()

    # 設定 Hudi 參數
    # 根據資源類型選擇合適的 precombine field
    precombine_field_map = {
        'Patient': 'lastModified',
        'Practitioner': 'lastModified',
        'Organization': 'lastModified',
        'Encounter': 'periodStart',
        'Observation': 'effectiveDateTime',
        'Condition': 'recordedDate'
    }

    precombine_field = precombine_field_map.get(resource_type, 'lastModified')
    table_name = f'fhir_{resource_type.lower()}'

    hudi_options = {
        'hoodie.table.name': table_name,
        'hoodie.datasource.write.recordkey.field': 'id',
        'hoodie.datasource.write.precombine.field': precombine_field,
        'hoodie.datasource.write.partitionpath.field': 'resourceType',
        'hoodie.datasource.write.operation': 'upsert',
        'hoodie.datasource.write.table.type': 'COPY_ON_WRITE',
        'hoodie.upsert.shuffle.parallelism': 2,
        'hoodie.insert.shuffle.parallelism': 2,
        # 啟用 Hive 同步，讓 Trino 可以查詢
        'hoodie.datasource.hive_sync.enable': 'true',
        'hoodie.datasource.hive_sync.database': 'default',
        'hoodie.datasource.hive_sync.table': table_name,
        'hoodie.datasource.hive_sync.partition_fields': 'resourceType',
        'hoodie.datasource.hive_sync.mode': 'hms',
        'hoodie.datasource.hive_sync.metastore.uris': 'thrift://localhost:9083'
    }

    # 寫入 Hudi table
    hdfs_path = f"hdfs://namenode:9000/user/hive/warehouse/{table_name}"

    df.write.format("hudi") \
        .options(**hudi_options) \
        .mode("overwrite") \
        .save(hdfs_path)

    print(f"✅ {resource_type} data written to Hudi at {hdfs_path}")

print("\n" + "="*60)
print("✅ All FHIR resources written to Hudi successfully!")
print("="*60)
spark.stop()
