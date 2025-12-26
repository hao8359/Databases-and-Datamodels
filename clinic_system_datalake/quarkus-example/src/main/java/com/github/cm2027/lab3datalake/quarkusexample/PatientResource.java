package com.github.cm2027.lab3datalake.quarkusexample;

import jakarta.inject.Inject;
import jakarta.ws.rs.GET;
import jakarta.ws.rs.Path;
import jakarta.ws.rs.Produces;
import jakarta.ws.rs.core.MediaType;
import jakarta.ws.rs.core.Response;
import org.apache.spark.sql.Dataset;
import org.apache.spark.sql.Row;
import org.apache.spark.sql.SparkSession;
import org.jboss.logging.Logger;

import com.github.cm2027.lab3datalake.quarkusexample.config.SparkConfig;

import java.time.Duration;
import java.time.Instant;
import java.util.List;

@Path("/patients")
public class PatientResource {

    private static final Logger LOG = Logger.getLogger(PatientResource.class);

    @Inject
    SparkSession spark;

    @Inject
    SparkConfig cfg;

    @GET
    @Produces(MediaType.APPLICATION_JSON)
    public Response getAllPatients() {
        Instant requestStart = Instant.now();
        String path = "/patients";
        String method = "GET";
        int statusCode = 500;
        int patientCount = 0;

        try {
            Dataset<Row> patientsDf = spark.read().format("hudi")
                    .load(cfg.getHdfsBaseUri() + "/fhir/patients-json");
            patientsDf.createOrReplaceTempView("patients");

            List<String> patients = spark.sql("SELECT * FROM patients").toJSON().collectAsList();
            patientCount = patients.size();
            statusCode = 200;

            String jsonArray = "[" + String.join(",", patients) + "]";
            return Response.ok(jsonArray, MediaType.APPLICATION_JSON).build();
        } catch (Exception ex) {
            LOG.errorf(ex, "Failed to handle request %s %s", method, path);
            return Response.status(Response.Status.INTERNAL_SERVER_ERROR)
                    .entity("Error fetching patients").build();
        } finally {
            Duration duration = Duration.between(requestStart, Instant.now());
            LOG.infof("%s %s -> status=%d, patients=%d, duration=%dms",
                    method, path, statusCode, patientCount, duration.toMillis());
        }
    }
}
