package com.github.cm2027.lab3datalake;

import com.github.cm2027.lab3datalake.hacks.TrinoHistoryFix;

public class CreateJSON {

    public static void main(String[] args) {
        var spark = Session.get();

        var path = "/fhir/patients-json";

        var df = spark
                .read()
                .option("multiline", "true")
                .json("./data/patient-*.json");

        df.write()
                .format("hudi")
                .option("hoodie.datasource.write.recordkey.field", "id")
                .option("hoodie.datasource.write.partitionpath.field", "resourceType")
                .option("hoodie.table.name", "fhir_raw_patient")
                .option("hoodie.table.type", "COPY_ON_WRITE")

                .option("hoodie.database.name", "default")
                .option("hoodie.datasource.hive_sync.mode", "hms")
                .option("hoodie.datasource.meta.sync.enable", "true")
                .option("hoodie.datasource.hive_sync.metastore.uris",
                        Session.HIVE_META_URI)

                // part of preventing a trino bug (explained later)
                .option("hoodie.archivelog.enable", "false")

                .mode("append")
                // We have access from spark to the hdfs server (the namenode)
                // so we can tell spark to write to that URI.
                .save(Session.HDFS_BASE_URI + path);

        // prevent trino bug, trino fails if history folder (in
        // /fhir/patients-json/.hoodie/timeline/) exists and is empty
        try {
            TrinoHistoryFix.ensureEmptyHistoryDeleted(path);
        } catch (Exception e) {
            System.out.println("Exception when trying to delete empty history directory on hdfs, path: " +
                    path);
        }
    }

}
