from pyspark.sql import SparkSession

# 初始化 Spark Session
spark = SparkSession.builder \
    .appName("FHIR-Hudi-Read") \
    .config("spark.jars.packages", "org.apache.hudi:hudi-spark3.5-bundle_2.12:1.0.2") \
    .config("spark.serializer", "org.apache.spark.serializer.KryoSerializer") \
    .config("spark.sql.extensions", "org.apache.spark.sql.hudi.HoodieSparkSessionExtension") \
    .config("spark.sql.catalog.spark_catalog", "org.apache.spark.sql.hudi.catalog.HoodieCatalog") \
    .config("spark.sql.hive.convertMetastoreParquet", "false") \
    .config("spark.sql.legacy.timeParserPolicy", "LEGACY") \
    .getOrCreate()

# FHIR 資源類型列表
resource_types = ['Patient', 'Practitioner', 'Organization', 'Encounter', 'Observation', 'Condition']

print("="*80)
print("Reading FHIR Data from Hudi Tables")
print("="*80)

for resource_type in resource_types:
    table_name = f'fhir_{resource_type.lower()}'
    hdfs_path = f"hdfs://namenode:9000/user/hive/warehouse/{table_name}"

    print(f"\n{'='*80}")
    print(f"📋 {resource_type} Table")
    print(f"{'='*80}")

    try:
        # 讀取 Hudi table
        df = spark.read.format("hudi").load(hdfs_path)

        print(f"Total records: {df.count()}")
        print(f"\nSchema:")
        df.printSchema()

        print(f"\nSample data:")
        df.show(truncate=False)

    except Exception as e:
        print(f"❌ Error reading {resource_type}: {str(e)}")

# 進階查詢範例
print("\n" + "="*80)
print("📊 Advanced Query Examples")
print("="*80)

# 1. 查詢特定病患的所有就診記錄
print("\n1️⃣ Patient's Encounters:")
print("-" * 80)
try:
    encounters_df = spark.read.format("hudi").load("hdfs://namenode:9000/user/hive/warehouse/fhir_encounter")
    patient_encounters = encounters_df.filter(encounters_df.subject == "Patient/patient-1")
    patient_encounters.select("id", "status", "periodStart", "subject", "practitioner").show(truncate=False)
except Exception as e:
    print(f"Error: {e}")

# 2. 查詢某個病患的所有觀察記錄
print("\n2️⃣ Patient's Observations:")
print("-" * 80)
try:
    obs_df = spark.read.format("hudi").load("hdfs://namenode:9000/user/hive/warehouse/fhir_observation")
    patient_obs = obs_df.filter(obs_df.subject == "Patient/patient-1")
    patient_obs.select("id", "codeText", "valueString", "effectiveDateTime").show(truncate=False)
except Exception as e:
    print(f"Error: {e}")

# 3. 統計每個醫生的就診次數
print("\n3️⃣ Encounters per Practitioner:")
print("-" * 80)
try:
    encounters_df = spark.read.format("hudi").load("hdfs://namenode:9000/user/hive/warehouse/fhir_encounter")
    encounters_df.groupBy("practitioner").count().orderBy("count", ascending=False).show(truncate=False)
except Exception as e:
    print(f"Error: {e}")

# 4. 查詢所有活躍的診所
print("\n4️⃣ Active Organizations:")
print("-" * 80)
try:
    org_df = spark.read.format("hudi").load("hdfs://namenode:9000/user/hive/warehouse/fhir_organization")
    active_orgs = org_df.filter(org_df.active == True)
    active_orgs.select("id", "name", "phone", "email", "address").show(truncate=False)
except Exception as e:
    print(f"Error: {e}")

print("\n" + "="*80)
print("✅ Query completed successfully!")
print("="*80)

spark.stop()
