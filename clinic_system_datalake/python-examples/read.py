#!/usr/bin/env python3

from session import spark, hdfs_base_uri

spark.read.format("hudi").load(
    hdfs_base_uri+"/fhir/patients-json").createOrReplaceTempView("patients")

print("===Patients===")
spark.sql("""
SELECT * FROM patients
""").show()

print("===IDs of Patients born on 1971-09-30===")
spark.sql("""SELECT id FROM PATIENTS WHERE birthDate = '1971-09-30'""").show()
