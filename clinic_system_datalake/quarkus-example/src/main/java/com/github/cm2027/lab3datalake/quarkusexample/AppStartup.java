package com.github.cm2027.lab3datalake.quarkusexample;

import com.github.cm2027.lab3datalake.quarkusexample.provider.SparkSessionProvider;

import io.quarkus.runtime.Startup;
import jakarta.annotation.PostConstruct;
import jakarta.enterprise.context.ApplicationScoped;
import jakarta.inject.Inject;

@Startup
@ApplicationScoped
public class AppStartup {

    @Inject
    SparkSessionProvider sparkSessionProvider;

    @PostConstruct
    void onStart() {

        // init sparksession on startup, remove if lazy init is wanted
        sparkSessionProvider.init();
    }
}
