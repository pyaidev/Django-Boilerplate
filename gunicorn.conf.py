import os

bind = "0.0.0.0:8000"
workers = int(os.getenv("WEB_CONCURRENCY", "2"))
worker_class = "gthread"
threads = int(os.getenv("WEB_THREADS", "2"))
timeout = 60
graceful_timeout = 30
max_requests = 2000
max_requests_jitter = 200
# App request logs use route names so reset tokens and query strings aren't logged.
accesslog = None
errorlog = "-"
capture_output = True
preload_app = False


def when_ready(server):
    from prometheus_client import CollectorRegistry, multiprocess, start_http_server

    registry = CollectorRegistry()
    multiprocess.MultiProcessCollector(registry)
    start_http_server(9000, addr="0.0.0.0", registry=registry)


def child_exit(server, worker):
    from prometheus_client import multiprocess

    multiprocess.mark_process_dead(worker.pid)
