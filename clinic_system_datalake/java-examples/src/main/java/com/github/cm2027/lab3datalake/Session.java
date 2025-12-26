package com.github.cm2027.lab3datalake;

import org.apache.spark.sql.SparkSession;

public class Session {

    private static SparkSession localInstance = null;

    // toggle for running spark compute locally or just submitting to
    // spark master => delegated to spark worker
    public static final boolean local = true;

    public static final String sparkMaster = local ? "local[*]" : "spark://localhost:7077";

    @SuppressWarnings("unused")
    public static final String HDFS_BASE_URI = "" != "local[*]" ? "hdfs://namenode:8020"
            : "hdfs://localhost:8020";

    @SuppressWarnings("unused")
    public static final String HIVE_META_URI = sparkMaster != "local[*]" ? "thrift://hivemetastore:9083"
            : "thrift://localhost:9083";

    public static synchronized SparkSession get() {
        if (localInstance == null) {
            return localInstance = SparkSession.builder()
                    .appName("hudi_example_fhir_etl")
                    // will make spark run on the machine running this code
                    // if you want to run this on a spark worker you can change this to the spark
                    // master URL
                    .master(sparkMaster)
                    .config("spark.jars.packages",
                            "org.apache.hudi:hudi-spark3.5-bundle_2.12:1.0.2," +
                                    "org.apache.hudi:hudi-hive-sync-bundle:1.0.2")
                    .enableHiveSupport()
                    .config("spark.sql.hive.convertMetastoreParquet", "false")
                    .config("spark.serializer", "org.apache.spark.serializer.KryoSerializer")
                    .config("spark.sql.catalog.spark_catalog", "org.apache.spark.sql.hudi.catalog.HoodieCatalog")
                    .config("spark.sql.extensions", "org.apache.spark.sql.hudi.HoodieSparkSessionExtension")
                    .config("spark.sql.legacy.timeParserPolicy", "LEGACY")
                    .getOrCreate();
        }
        return localInstance;
    }

    public static void main(String[] args) {
        get();
    }

}
