package com.github.cm2027.lab3datalake.quarkusexample;

import com.github.cm2027.lab3datalake.quarkusexample.config.SparkConfig;
import jakarta.inject.Inject;
import jakarta.ws.rs.GET;
import jakarta.ws.rs.Path;
import jakarta.ws.rs.Produces;
import jakarta.ws.rs.core.MediaType;
import jakarta.ws.rs.core.Response;
import org.apache.hadoop.conf.Configuration;
import org.apache.hadoop.fs.FileSystem;
import org.apache.spark.sql.SparkSession;
import org.jboss.logging.Logger;

import java.net.URI;
import java.util.HashMap;
import java.util.Map;

@Path("/healthz")
public class HealthResource {

    private static final Logger LOG = Logger.getLogger(HealthResource.class);

    @Inject
    SparkSession spark;

    @Inject
    SparkConfig config;

    @GET
    @Produces(MediaType.APPLICATION_JSON)
    public Response healthCheck() {
        Map<String, Object> status = new HashMap<>();
        boolean overallHealthy = true;

        Map<String, Object> sparkStatus = new HashMap<>();
        try {
            long start = System.currentTimeMillis();
            spark.sql("SELECT 1").collect();
            long end = System.currentTimeMillis();
            sparkStatus.put("status", "UP");
            sparkStatus.put("responseTimeMs", end - start);
        } catch (Exception e) {
            LOG.error("Spark health check failed", e);
            sparkStatus.put("status", "DOWN");
            sparkStatus.put("error", e.getMessage());
            overallHealthy = false;
        }
        status.put("spark", sparkStatus);

        Map<String, Object> hdfsStatus = new HashMap<>();
        try {
            long start = System.currentTimeMillis();
            Configuration hadoopConf = new Configuration();
            try (FileSystem fs = FileSystem.get(new URI(config.getHdfsBaseUri()), hadoopConf)) {
                boolean accessible = fs.exists(new org.apache.hadoop.fs.Path("/"));
                long end = System.currentTimeMillis();
                hdfsStatus.put("status", accessible ? "UP" : "DOWN");
                hdfsStatus.put("responseTimeMs", end - start);
                if (!accessible)
                    overallHealthy = false;
            }
        } catch (Exception e) {
            LOG.error("HDFS health check failed", e);
            hdfsStatus.put("status", "DOWN");
            hdfsStatus.put("error", e.getMessage());
            overallHealthy = false;
        }
        status.put("hdfs", hdfsStatus);

        status.put("status", overallHealthy ? "UP" : "DOWN");

        return Response.status(overallHealthy ? Response.Status.OK : Response.Status.SERVICE_UNAVAILABLE)
                .entity(status)
                .type(MediaType.APPLICATION_JSON) // ensure JSON content-type
                .build();
    }
}
