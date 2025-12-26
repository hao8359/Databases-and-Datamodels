package com.github.cm2027.lab3datalake.quarkusexample.provider;

import com.github.cm2027.lab3datalake.quarkusexample.config.SparkConfig;
import jakarta.annotation.PostConstruct;
import jakarta.annotation.PreDestroy;
import jakarta.enterprise.context.ApplicationScoped;
import jakarta.enterprise.inject.Produces;
import jakarta.inject.Inject;
import org.apache.spark.SparkConf;
import org.apache.spark.sql.SparkSession;
import org.jboss.logging.Logger;

@ApplicationScoped
public class SparkSessionProvider {

    private static final Logger LOG = Logger.getLogger(SparkSessionProvider.class);

    private SparkSession sparkSession;

    @Inject
    SparkConfig config;

    /**
     * Initialize SparkSession on application startup (main thread)
     */
    @PostConstruct
    public void init() {
        LOG.info("Initializing SparkSession on main thread...");

        try {
            SparkConf cfg = new SparkConf(true)
                    .setMaster(config.getSparkMaster())
                    .setAppName(config.getAppName())
                    .set("spark.jars.packages", config.getJarsPackages())
                    .set("spark.ui.enabled", "false")
                    .set("spark.sql.hive.convertMetastoreParquet", "false")
                    .set("spark.serializer", "org.apache.spark.serializer.KryoSerializer")
                    .set("spark.sql.catalog.spark_catalog", "org.apache.spark.sql.hudi.catalog.HoodieCatalog")
                    .set("spark.sql.extensions", "org.apache.spark.sql.hudi.HoodieSparkSessionExtension")
                    .set("spark.sql.legacy.timeParserPolicy", "LEGACY");

            sparkSession = SparkSession.builder()
                    .config(cfg)
                    .getOrCreate();

            LOG.info("SparkSession created successfully on main thread.");
        } catch (Exception e) {
            LOG.error("Failed to initialize SparkSession", e);
            throw new RuntimeException("SparkSession initialization failed", e);
        }
    }

    /**
     * Produce SparkSession for injection
     */
    @Produces
    @ApplicationScoped
    public SparkSession produceSparkSession() {
        if (sparkSession == null) {
            throw new IllegalStateException(
                    "SparkSessionProvider not initialized. This should never happen if @PostConstruct worked.");
        }
        return sparkSession;
    }

    /**
     * Shutdown hook to stop SparkSession when Quarkus shuts down.
     */
    @PreDestroy
    public void close() {
        if (sparkSession != null) {
            LOG.info("Stopping SparkSession...");
            sparkSession.stop();
            LOG.info("SparkSession stopped.");
        }
    }
}
