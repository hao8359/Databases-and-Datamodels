package com.github.cm2027.lab3datalake.quarkusexample.config;

import io.quarkus.runtime.annotations.StaticInitSafe;
import org.eclipse.microprofile.config.inject.ConfigProperty;

import jakarta.enterprise.context.ApplicationScoped;
import lombok.Getter;

@StaticInitSafe
@ApplicationScoped
@Getter
public class SparkConfig {

    @ConfigProperty(name = "spark.master", defaultValue = "local[*]")
    String sparkMaster;

    @ConfigProperty(name = "spark.app-name", defaultValue = "hudi_example_fhir_quarkus")
    String appName;

    @ConfigProperty(name = "spark.hdfs.base-uri", defaultValue = "hdfs://localhost:8020")
    String hdfsBaseUri;

    @ConfigProperty(name = "spark.hive.meta-uri", defaultValue = "thrift://localhost:9083")
    String hiveMetaUri;

    @ConfigProperty(name = "spark.jars.packages", defaultValue = "org.apache.hudi:hudi-spark3.5-bundle_2.12:1.0.2,org.apache.hudi:hudi-hive-sync-bundle:1.0.2")
    String jarsPackages;
}
