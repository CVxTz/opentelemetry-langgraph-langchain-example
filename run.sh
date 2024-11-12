export $(cat .env | xargs)
# opentelemetry-bootstrap -a install
PYTHONPATH=. opentelemetry-instrument --logs_exporter otlp python fastapi_langgraph/app.py