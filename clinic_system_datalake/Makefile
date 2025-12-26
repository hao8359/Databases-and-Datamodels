compose_file ?= local.compose.yaml
JAVA_EXAMPLES_JAR = java-examples/target/java-examples-1.0-SNAPSHOT.jar
JAVA_SRC = $(shell find java-examples/src -name "*.java")

DC_ARGS ?=

.PHONY: help
help: ## Show this help
	@echo "Usage: make <target> [DC_ARGS=\"<docker-compose args>\"]"
	@echo ""
	@echo "Hint:"
	@echo "  To get started run: make clean up logs"
	@echo ""
	@echo "Targets:"
	@grep -E '^[a-zA-Z0-9_/-]+:.*?## .*$$' $(MAKEFILE_LIST) \
		| sort -f \
		| awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-25s\033[0m %s\n", $$1, $$2}'

.DEFAULT_GOAL := help

.PHONY: logs
logs: ## Check logs from the datalake
	@docker compose -f $(compose_file) logs -f $(DC_ARGS)

.PHONY: up
up: ## Spin up the docker compose for the datalake
	@docker compose -f $(compose_file) up -d $(DC_ARGS)
	@echo "[TIP] You can run make logs to see logs"

.PHONY: down
down: ## Stop running instances of the compose for the datalake
	@docker compose -f $(compose_file) down $(DC_ARGS)

.PHONY: clean
clean: ## Wipe all persisted data
	@docker compose -f $(compose_file) down -v --remove-orphans $(DC_ARGS)

.PHONY: java
java/%: $(JAVA_EXAMPLES_JAR)
	@spark-submit \
		--class com.github.cm2027.lab3datalake.$* \
		--master "local[0]" \
		--conf "spark.jars.packages"="org.apache.hudi:hudi-spark3.5-bundle_2.12:1.0.2" \
		$(JAVA_EXAMPLES_JAR)

$(JAVA_EXAMPLES_JAR): $(JAVA_SRC)
	@echo "Building Java shaded JAR..."
	@mvn -f java-examples/pom.xml package -DskipTests

.PHONY: python
python/%:
	@./python-examples/$*

.PHONY: java/create java/read python/create python/read

java/create: java/CreateJSON ## Run the java example to upload the patients in the ./data dir to the datalake
	@true

java/read: java/Read ## Run the java example to read the uploaded patients from the data lake
	@true

#python/create: python/create_json.py ## Run the python example to upload the patients in the ./data dir to the datalake
#	@true

#python/read: python/read.py ## Run the python example to read the uploaded patients from the data lake
#	@true
python/create:
	docker compose -f local.compose.yaml run --rm sparkmaster \
		spark-submit \
		--master spark://sparkmaster:7077 \
		--packages org.apache.hudi:hudi-spark3.5-bundle_2.12:1.0.2 \
		--conf spark.serializer=org.apache.spark.serializer.KryoSerializer \
		--conf spark.sql.extensions=org.apache.spark.sql.hudi.HoodieSparkSessionExtension \
		--conf spark.sql.catalog.spark_catalog=org.apache.spark.sql.hudi.catalog.HoodieCatalog \
		--conf spark.sql.hive.convertMetastoreParquet=false \
		--conf spark.sql.legacy.timeParserPolicy=LEGACY \
		/opt/spark-apps/create_fhir_hudi_fixed.py

python/read:
	docker compose -f local.compose.yaml run --rm sparkmaster \
		spark-submit \
		--master spark://sparkmaster:7077 \
		--packages org.apache.hudi:hudi-spark3.5-bundle_2.12:1.0.2 \
		--conf spark.serializer=org.apache.spark.serializer.KryoSerializer \
		--conf spark.sql.extensions=org.apache.spark.sql.hudi.HoodieSparkSessionExtension \
		--conf spark.sql.catalog.spark_catalog=org.apache.spark.sql.hudi.catalog.HoodieCatalog \
		--conf spark.sql.hive.convertMetastoreParquet=false \
		--conf spark.sql.legacy.timeParserPolicy=LEGACY \
		/opt/spark-apps/read_fhir_hudi_fixed.py



trino: ## Use trino to query for patients
	@cd trino-client && \
		go run main.go
