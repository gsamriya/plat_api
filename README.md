# plat-api

A lightweight, production-ready FastAPI service template. It supports robust API development with built-in logging, monitoring, authentication, configuration via YAML, and optional Kafka integration.

---

## Features
plat-api is a specialized lightweight FastAPI service template, providing FastAPI features leveraged with enhanced logging(org-logger) and monitoring(org-monitor) functionalities developed at org, along with support for built-in authentication, validation, configuration via YAML, and optional Kafka integration. Its salient features are:

- **FastAPI** with async routes  
- **Basic and Token Authentication**
- **Validation support for query and body parameters via in-built Pydantic**
- **YAML-based Configuration**  
- **Prometheus based monitoring** via `prometheus_fastapi_instrumentator`
- **Integrated logging** via `org_logger` as middleware**
- **Supporting specialized or custom monitoring** via `org_monitor`, integrated as middleware
- **CI/CD** ready with GitLab  
- **Coverage Reports** using `pytest-cov`  
- **Dockerized** with `docker-compose` support
- **Publishes asynchronous requests to Kafka cluster** as optional feature
- Provides **Swagger** based end point documentation
---

## Project Structure

```
plat-api/
├── src/
│ └── __init__.py
│ └── org_api/
│   ├── app.py # FastAPI app factory
│   ├── config_loader.py # Loads YAML config
│   ├── auth.py # Basic & token authentication
│   ├── routes/
│   │ └── api_routing.py # GET /status,/metrics, POST /data
│   ├── kafka_client.py # Kafka async publisher
│   ├── run.py # Entrypoint script
│   ├── app.log # For logs by org_logger
│   ├── __init__py.py # For identifying org_api as a package
│   └── configs/
│       └── config.yaml # Default config file, with kafka disabled.
│       └── config_kafkaenabled.yaml # Config file, to be used when Kafka messaging is to be enabled
├── test/
│ ├── test_unit_api_logic.py # Unit tests for core logic
│ └── test_e2e.py # E2E tests with FastAPI TestClient
├── pyproject.toml # Dependencies and build config
├── Dockerfile # Docker build instructions
├── docker-compose.yml # Compose file for local dev
├── .gitlab-ci.yml # GitLab CI/CD pipeline
├── .gitignore # Files to ignore in git
├── .dockerignore # Files to ignore in Docker
├── coverage.xml # Coverage report output
└── README.md # This file
```
---

## Installation

1. **Clone the repository:**
    ```sh
    git clone https://git.org.ie/platform-engineering/plat-api.git
    cd plat-api
    ```

2. **Create and activate a virtual environment (recommended):**
    ```sh
    python3 -m venv .venv
    source .venv/bin/activate
    ```

3. **Install dependencies:**
    ```sh
    pip install .[dev]
    ```

4. **Run locally with default config**
    ```sh
    PYTHONPATH=./src python src/org_api/run.py
    ```
5. **Alternatively, Docker Usage**

    Build & Run:
     ```sh
    docker build -t plat-api .
    docker run -e org_FASTAPI_CONFIG=config.yaml -p 8000:8000 plat-api
    ```
    Or use Docker Compose:
    ```sh
    docker compose up --build
    ```
---

## Usage

```python
from org_api import create_app

app = create_app()

```
---
### Configuration

All runtime settings are to be defined in a YAML file, which can be set via method argument, environment variable or CLI.
The module provides two YAML files [`src/org_api/configs`](src/org_logger/configs/) currently as examples:
- `config.yaml`: This is default configuration file, used in case no other configuration file is specified. Specified API server host and port, with no kafka support.
- `config_kafkaenabled.yaml`: Enables kafka handler and specifies kafka bootstrap server and topic, in addition to specifying API server host and port as well.

### 1. Passing config via argument:
You can set a configuration, by passing it as an argument to the method `create_app` as shown below:

```python
#for using kafka enabling configuration file
app = create_app(config_file="config_kafkaenabled.yaml")
```
or
```python
#for user specified configuration file, kept at any path 
app = create_app(config_file="path/to/Yaml_file.yaml")
```
or
```python
#for using default configuration file - config.yaml
app = create_app()  #no method arg passed
#or
app = create_app(config_file="config.yaml")
```

### 2. Set the config file through CLI (Optional Prerequisite):
The module allows overriding of configuration via CLI.
```sh
# via CLI argument
python src/org_api/run.py --config=path/to/config.yaml
```

### 3. Set the config file through env variable (Optional Prerequisite):
```sh
# via env var
export CONFIG=path/to/config.yaml
```
The order of precedence for configuration files is Via Argument >> Via CLI >> Via Env variable

---

## Access API:

- GET http://localhost:8000/status
- GET http://localhost:8000/metrics
- POST http://localhost:8000/data

### Use Authentication:
All the endpoints are protected with authentication, allowing only authorized users to get successful response
The app currently supports Basic authentication and Token based authentication, either providing effective authentication. A user can use either or both of them to get authenticated.
1. HTTP Basic
Username: admin
Password: secret

2. Token Based
Token: supersecrettoken

### Curl Examples to test the application

```sh
curl -u admin:secret http://localhost:8000/status
```
```sh
curl -X POST http://localhost:8000/data \
  -u admin:secret \
  -H "Content-Type: application/json" \
  -d '{"key": "value"}'
```
---
## Run Tests
Run unit + E2E tests, coverage report will be available in coverage.xml. Unit test cases have been implemented for multiple functionalities of the module, providing code coverage of more than 90% 
Also, E2E test cases are provided for both GET and POST endpoints of the module
```sh
pytest --cov=src
```

---

## CI/CD with GitLab
This project includes a ready-to-use .gitlab-ci.yml that:

- Creates isolated virtual environment
- Installs dependencies
- Builds package using pyproject.toml
- Runs tests + generates coverage
- Publishes artifacts to GitLab Package Registry

---
## Prometheus Monitoring
Exposes Prometheus-compatible /metrics endpoint secured with authentication, enabling safe collection of application metrics while preventing unauthorized access.

---
## Integration with `org-logger`

Uses the centralized org-logger utility as middleware for consistent, structured, and configurable logging across services, with support for stdout, file, and Elasticsearch sinks. The utility is imported via custom index url provided by the utility Gitlab registry.

---
## Integration with `org-monitor`

Seamlessly integrates with the org-monitor package as middleware to enable real-time customised and advanced metrics collection using Prometheus. As example, a custom request counter 'http_requests_total_org_api' is initialized with labeled dimensions such as HTTP method and endpoint. Monitoring is handled via the MonitoringMiddleware class, which automatically increments counters for specific routes (e.g., /status, /data) on every request.
The metrics are exposed at the /metrics endpoint and are compatible with Prometheus scraping and Grafana visualization, allowing for robust observability and performance tracking across deployments.

---
## Publishing asynchronous requests to Kafka cluster

To enable publishing asynchronous requests to Kafka cluster:

1. Use the `config_kafkaenable.yaml` config or enable kafka handler in your YAML config.
2. Update bootstrap server and topic for Kafka in your config. Ensure that topic is already created and kafka is running on the mentioned server.
3. Ensure Kafka cluster and Kafka consumer are running as prerequisite, prior to launching the application.
4. Launch the plat-api application, and then do GET & POST calls (you can use Swagger or curl for it).
5. Read messages at Kafka consumer, the request messages regarding API calls should be visible at Kafka consumer.
---
## Documents endpoints in Swagger YAML

The module provides full API documentation using a Swagger-compliant OpenAPI YAML file. This enables clear, structured, and version-controlled specifications for all endpoints. The documentation is automatically rendered using FastAPI’s interactive Swagger UI, allowing developers and users to explore available routes, request/response schemas, and authentication methods directly in the browser.

Interactive Docs: http://localhost:8000/docs

This makes it easy to test APIs, generate client SDKs, and ensure consistent interface definitions across environments.

---
## Support
For issues or contributions, contact: `platformengineering@org.ie`
