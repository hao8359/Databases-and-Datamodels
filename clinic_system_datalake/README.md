> [!IMPORTANT]
> Work In Progress

# Lab 3 datalake

## Table of contents

- [Introduction](#introduction)
    - [Data Lake](#data-lake)
    - [Data Warehouse](#data-warehouse)
    - [Storage](#storage)
    - [Apache Hudi](#apache-hudi)
    - [Query Engines](#query-engines)
        - [Apache Spark](#apache-spark)
        - [Trino](#trino)
        - [Apache Hive](#apache-hive)
- [Compose Files](#compose-files)
- [Code Examples](#code-examples)
    - [Java](#java)
        - [Java Examples](#java-examples)
    - [Python](#python)
        - [Python Examples](#python-examples)
- [Getting Started](#getting-started)
    - [Open in devcontainer](#0-open-this-repository-in-the-devcontainer)
    - [Start datalake in devcontainer](#1-start-the-data-lake-environment)
    - [Run examples](#2-run-examples)
        - [Java examples](#run-java-examples)
        - [Python examples](#run-python-examples)
    - [Tear down](#3-tear-down)

## Introduction

Modern data platforms have to do two things at once: store tons of raw, flexible data, and let you query it fast for analytics. Data lakes handle the first part, data warehouses handle the second. Apache Hudi connects the two by adding transactional support and near real-time querying directly on data lake storage => data lakehouse.

### Data Lake

A data lake is a central place to store all kinds of data. Structured or unstructured. Data stays in its original format, making it easy to gather and process large, varied datasets. Data lakes are commonly used for analytics, machine learning, and big data processing.

### Data Warehouse

Data warehouses are all about structured data and fast queries. They use schema-on-write, which keeps things consistent and speeds up queries but makes the system less flexible. Warehouses work well for business intelligence but aren’t ideal for streaming or fast-changing data.

### Storage

In a data lake setup, the **storage layer** holds raw and processed data. Apache Hudi works on top of distributed or object storage like:

* **HDFS (Hadoop Distributed File System)** – A distributed storage system that runs on regular hardware. It offers high-throughput access and is often used in on-prem Hadoop setups.
* **S3 (Simple Storage Service)** – Scalable object storage from AWS. Open-source alternatives like [MinIO](https://min.io/) let you use the S3 API on self-hosted or hybrid setups.

### Apache Hudi

**[Apache Hudi](https://hudi.apache.org/)** (Hadoop Upserts Deletes and Incrementals) is an open-source framework that adds transactional features to your data lake. It manages how data is written, updated, and queried, bridging the gap between ingestion and analytics.

Hudi works with storage systems like [HDFS](https://hadoop.apache.org/docs/stable/hadoop-project-dist/hadoop-hdfs/HdfsDesign.html) or [S3](https://aws.amazon.com/s3/) and plays nicely with Spark, Trino, and Hive.

* [Hudi docs](https://hudi.apache.org/docs/overview/)
* [Hudi quick start guide](https://hudi.apache.org/docs/quick-start-guide)

### Query Engines

Hudi tables can be queried using different engines depending on what the use-case is.

#### Apache Spark

**Spark** handles most of Hudi’s writes and compactions. It supports batch and streaming ingestion, schema evolution, and heavy data transformations. Most Hudi operations like upserts and cleaning run as Spark jobs.

* [Spark docs](https://spark.apache.org/docs//3.5.0/)

#### Trino

**Trino** (formerly PrestoSQL) is a distributed SQL engine for fast analytics over large datasets. It can read Hudi tables directly, so you don’t have to move data into a warehouse.

In tests, Trino is much faster than Spark (~200-500ms vs multiple seconds), but it’s read-only. The Hudi connector can have bugs, like failing when the Hudi archive folder exists. In this examples, we use [this workaround](./java-examples/src/main/java/com/github/cm2027/lab3datalake/hacks/TrinoHistoryFix.java) to handle it.

* [Trino docs](https://trino.io/docs/476/)
* [Trino + Hudi](https://trino.io/docs/467/connector/hudi.html)

#### Apache Hive

**Hive** offers a traditional SQL interface for batch processing and metadata management. Hudi integrates with Hive to sync table schemas and partitions, so it works with existing Hadoop and Hive setups, this is needed for things like trino to be able to query hudi.

* [Hive docs](https://hive.apache.org/docs/latest/)

## Compose Files

This repository includes five[^*] different Docker Compose configurations that define various parts of the data-lake setup.

* [`base.compose.yaml`](./base.compose.yaml):
  Defines the **core data lake components**, such as the [`namenode` and `datanode`](https://hadoop.apache.org/docs/r1.2.1/hdfs_design.html#NameNode+and+DataNodes). It also includes services required for **Hive** and **Spark**, like [`sparkmaster`]() and [`spark-worker-1`]().

* [`hive.compose.yaml`](./hive.compose.yaml):
  Includes services required for **Hive**.

* [`spark.compose.yaml`](./spark.compose.yaml):
  Adds **Spark**, [`sparkmaster`]() and [`spark-worker-1`]().

* [`trino.compose.yaml`](./trino.compose.yaml):
  Adds optional services needed to enable **[Trino](https://trino.io/)** as a high-performance SQL query engine for interactive reads on the data lake.

* [`local.compose.yaml`](./local.compose.yaml):
  Wraps both the other compose files + adds a `traefik` reverse proxy.

---

[^*]: There are actually six different docker compose configurations, but the last one is only used for deploying to [the cloud](https://cloud.cbh.kth.se/) with the [`kthcloudw`](./kthcloudw) wrapper script.

## Code Examples

This repository includes code examples in both **Java** and **Python**, demonstrating how to perform read/write operations on the data lake using **Apache Spark** and **Apache Hudi**.

### [Java Examples](./java-examples)

These examples demonstrate how to use Spark with Java to interact with the data lake.

#### Examples

* [**Create JSON**](./java-examples/src/main/java/com/github/cm2027/lab3datalake/CreateJSON.java)
  Demonstrates how to upload JSON data to the data lake using Spark.
  This example runs Spark locally for simplicity, but in production it’s more common to **submit Spark jobs** to a Spark master, which then distributes tasks to Spark workers.
  In that case, the input data would need to be accessible to the workers for example, by storing it in **HDFS** or an **S3 bucket**.

* [**Read**](./java-examples/src/main/java/com/github/cm2027/lab3datalake/Read.java)
  Shows how to read Hudi tables using Spark from Java.

> [!IMPORTANT]
> Spark + Hudi *should* work with Java 8, 11, and 17.
> However, since some internal classes have changed in newer JVM versions, **additional JVM arguments** are required for Java 17.
> These are already configured as environment variables in the [devcontainer configuration](.devcontainer/devcontainer.json), so everything should work automatically when running inside the devcontainer.

### [Python Examples](./python-examples)

The Python examples use **[PySpark](https://spark.apache.org/docs/latest/api/python/)**, which allows Spark to be controlled directly from Python.
Under the hood, PySpark uses **[Py4J](https://www.py4j.org/)** to communicate with the underlying Spark JVM process, so a compatible JVM and Spark installation are required.
This environment is already configured in the devcontainer.

#### Examples

* [**Create JSON**](./python-examples/create_json.py)
* [**Read**](./python-examples/read.py)

### [Trino](./trino-client)

There is a trino client example that just shows an alternative to spark.

> [!NOTE]
> Trino has support for many languages, this example is written in [go](https://go.dev/) 
> but it could be used in languages like [Java](https://trino.io/docs/current/client/jdbc.html) too.

#### Examples

* [**Read**](./trino-client/main.go)

## Getting Started

You can run the examples directly from the devcontainer.

### 0. Open this repository in the devcontainer

#### Prerequisites

- docker
- vs-code
- [vs-code remote development extension](https://marketplace.visualstudio.com/items?itemName=ms-vscode-remote.vscode-remote-extensionpack)

Then, open the repository in **VS Code**, and press (`ctrl` + `shift` + `p`) or (`cmd`+ `shift`+ `p` on mac) and select `Dev Containers: Rebuild and Reopen in Container`.

### 1. Start the Data Lake Environment

```bash
make clean up logs
# clean and logs are optional
# logs will run "docker compose -f local.compose.yaml -f" to show all logs from the datalake in your c
```

### 2. Run examples

#### Run Java examples:

This will run the java examples for both creating and then reading

```bash
make java/create java/read
```

#### Run Python examples:

This will run the python examples for both creating and then reading

```bash
make python/create python/read
```

#### Run Trino example:

This will compile and run a trino client that performs the same queries that the spark read jobs did.

```bash
make trino
```

### 3. Tear Down

When you’re done:

```bash
make down # optionally add "clean" to remove all docker volumes
```
