package com.github.cm2027.lab3datalake;

import java.time.Duration;
import java.time.Instant;

public class Read {
    public static void main(String[] args) {
        var spark = Session.get();

        var patientsDataFrame = spark
                .read()
                .format("hudi")
                .load(Session.HDFS_BASE_URI + "/fhir/patients-json");
        patientsDataFrame.createOrReplaceTempView("patients");

        Instant start = Instant.now();

        System.out.println("===Patients===");

        spark.sql("SELECT * FROM PATIENTS").show();
        Instant end = Instant.now();
        Duration timeElapsed = Duration.between(start, end);
        System.out.println("SELECT * FROM PATIENTS took: " + timeElapsed.toMillis() + " ms");

        Instant start2 = Instant.now();

        System.out.println("===IDs of Patients born on 1971-09-30===");
        spark.sql("SELECT id FROM PATIENTS WHERE birthDate = '1971-09-30'").show(false);
        Instant end2 = Instant.now();
        Duration timeElapsed2 = Duration.between(start2, end2);
        System.out.println(
                "SELECT id FROM PATIENTS WHERE birthDate = '1971-09-30' took: " + timeElapsed2.toMillis() + " ms");

    }
}
