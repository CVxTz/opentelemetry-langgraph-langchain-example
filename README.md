# AI Agent Observability with OpenTelemetry and New Relic

This project demonstrates how to add observability to an AI agent built using **LangGraph** and **LangChain**, with traces, metrics, and logging centralized in **New Relic**. The observability framework relies on **OpenTelemetry** for instrumentation, allowing for detailed tracking and analysis of agent performance in real-time. This repository contains the source code, configuration files, and setup instructions to run and monitor an AI agent with minimal configuration.

## Features

- **Automatic Instrumentation** of popular Python libraries (e.g., FastAPI, Requests) using OpenTelemetry.
- **Custom Metrics** for tracking resource usage, such as input/output tokens of the LLM.
- **Traces and Spans** to monitor the AI agent’s individual operations and flow.
- **Centralized Monitoring** in New Relic for real-time insights and alerts on agent performance and resource usage.

## Prerequisites

- Python 3.9 or above
- A New Relic account (free tier available) and a New Relic License Key
- A compatible OpenTelemetry and Python setup

## Installation

1. **Clone the Repository**

   ```bash
   git clone https://github.com/CVxTz/opentelemetry-langgraph-langchain-example
   cd opentelemetry-langgraph-langchain-example
   ```

2. **Install Dependencies**

   Install the necessary Python packages, including OpenTelemetry and LangGraph:

   ```bash
   pip install -r requirements.txt
   ```

3. **Set Up Environment Variables**

   Create a `.env` file in the project root directory with the following content. Replace `YOUR_NEW_RELIC_LICENSE_KEY` with your actual New Relic license key:

   ```plaintext
   LLM_API_KEY=LLM_API_KEY
   OTEL_SERVICE_NAME=ot-llm-agent
   OTEL_RESOURCE_ATTRIBUTES=service.instance.id=123
   OTEL_PYTHON_LOGGING_AUTO_INSTRUMENTATION_ENABLED=true
   OTEL_EXPORTER_OTLP_ENDPOINT=https://otlp.eu01.nr-data.net
   OTEL_EXPORTER_OTLP_HEADERS=api-key=YOUR_NEW_RELIC_LICENSE_KEY
   OTEL_ATTRIBUTE_VALUE_LENGTH_LIMIT=4095
   OTEL_EXPORTER_OTLP_COMPRESSION=gzip
   OTEL_EXPORTER_OTLP_PROTOCOL=http/protobuf
   OTEL_EXPORTER_OTLP_METRICS_TEMPORALITY_PREFERENCE=delta
   OTEL_PYTHON_LOG_LEVEL=debug
   ```

## Running the Application

The `run.sh` script loads environment variables from `.env`, sets up OpenTelemetry instrumentation, and starts the application:

```bash
bash run.sh
```

Once running, you can make requests to the AI agent’s API (e.g., via FastAPI endpoints) and observe real-time telemetry data in your New Relic dashboard.

## Testing the Setup

1. **Send Requests to the Agent**: http://localhost:8080/docs
2. **View Data in New Relic**: Log in to your New Relic account and go to the Observability dashboard to view traces, spans, and metrics associated with your service.

## Example

The repository includes an example `query_llm` function, which demonstrates how to define nodes in LangGraph, instrument spans, and log token usage metrics.

## Resources

For more information, see the official New Relic OpenTelemetry example repository:  
[New Relic OpenTelemetry Python Guide](https://github.com/newrelic/newrelic-opentelemetry-examples/tree/main/getting-started-guides/python)
