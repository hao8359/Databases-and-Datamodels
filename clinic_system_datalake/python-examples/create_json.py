#!/usr/bin/env python3

from session import spark, hdfs_base_uri, hive_meta_uri

relative_data_path = "./data"

path = "/fhir/patients-json"

df = spark.read.option("multiline", "true").json(
    relative_data_path+"/patient-*.json")

df.write \
    .format("hudi") \
    .option("hoodie.datasource.write.recordkey.field", "id") \
    .option("hoodie.datasource.write.partitionpath.field", "resourceType") \
    .option("hoodie.table.name", "fhir_raw_patient") \
    .option("hoodie.table.type", "COPY_ON_WRITE") \
    .option("hoodie.database.name", "default") \
    .option("hoodie.datasource.hive_sync.mode", "hms") \
    .option("hoodie.datasource.meta.sync.enable", "true") \
    .option("hoodie.datasource.hive_sync.metastore.uris", hive_meta_uri) \
    .option("hoodie.archivelog.enable", "false") \
    .mode("append") \
    .save(hdfs_base_uri + path)
