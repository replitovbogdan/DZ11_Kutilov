import time
import random
import threading
from http.server import HTTPServer, BaseHTTPRequestHandler
from prometheus_client import (
    Counter, Gauge, Histogram, Summary,
    generate_latest, CONTENT_TYPE_LATEST, CollectorRegistry, REGISTRY
)

REQUEST_COUNT = Counter(
    'app_requests_total',
    'Total number of HTTP requests',
    ['method', 'endpoint', 'status']
)

REQUEST_LATENCY = Histogram(
    'app_request_duration_seconds',
    'HTTP request latency in seconds',
    ['endpoint'],
    buckets=[0.01, 0.05, 0.1, 0.25, 0.5, 1.0, 2.0]
)

ACTIVE_USERS = Gauge(
    'app_active_users',
    'Number of currently active users'
)

FILES_PROCESSED = Counter(
    'app_files_processed_total',
    'Total files processed by type',
    ['file_type', 'status']
)

PROCESSING_TIME = Summary(
    'app_file_processing_seconds',
    'Time spent processing files',
    ['file_type']
)

ERROR_COUNT = Counter(
    'app_errors_total',
    'Total number of application errors',
    ['error_type']
)

CPU_USAGE = Gauge('app_cpu_usage_percent', 'Simulated CPU usage percent')
MEMORY_USAGE = Gauge('app_memory_usage_bytes', 'Simulated memory usage in bytes')


def simulate_metrics():
    file_types = ['json', 'csv', 'unknown', 'xml']
    endpoints = ['/process', '/health', '/upload', '/status']
    errors = ['timeout', 'format_error', 'validation_error']

    while True:
        ACTIVE_USERS.set(random.randint(5, 50))
        CPU_USAGE.set(random.uniform(10, 85))
        MEMORY_USAGE.set(random.uniform(50 * 1024 * 1024, 300 * 1024 * 1024))

        for ep in endpoints:
            REQUEST_COUNT.labels(method='GET', endpoint=ep, status='200').inc(random.randint(1, 10))
            latency = random.uniform(0.01, 0.5)
            REQUEST_LATENCY.labels(endpoint=ep).observe(latency)

        for ft in file_types:
            count = random.randint(1, 20)
            FILES_PROCESSED.labels(file_type=ft, status='success').inc(count)
            proc_time = random.uniform(0.05, 2.0) if ft == 'unknown' else random.uniform(0.01, 0.1)
            PROCESSING_TIME.labels(file_type=ft).observe(proc_time)

        if random.random() < 0.3:
            err = random.choice(errors)
            ERROR_COUNT.labels(error_type=err).inc()
            REQUEST_COUNT.labels(method='POST', endpoint='/process', status='500').inc()

        time.sleep(3)


class MetricsHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path == '/metrics':
            output = generate_latest(REGISTRY)
            self.send_response(200)
            self.send_header('Content-Type', CONTENT_TYPE_LATEST)
            self.end_headers()
            self.wfile.write(output)
        elif self.path == '/health':
            self.send_response(200)
            self.send_header('Content-Type', 'text/plain')
            self.end_headers()
            self.wfile.write(b'OK - Microservice is running')
        else:
            self.send_response(200)
            self.send_header('Content-Type', 'text/html')
            self.end_headers()
            self.wfile.write(b'''
<html><head><title>Quality Monitoring App</title>
<style>body{font-family:Arial,sans-serif;margin:40px;background:#f5f5f5;}
.card{background:white;padding:20px;border-radius:8px;margin:10px 0;box-shadow:0 2px 4px rgba(0,0,0,0.1);}
h1{color:#333;}a{color:#1976d2;}</style></head>
<body>
<h1>Microservice Quality Monitoring</h1>
<div class="card"><h2>Endpoints</h2>
<p><a href="/metrics">/metrics</a> - Prometheus metrics</p>
<p><a href="/health">/health</a> - Health check</p>
</div>
<div class="card"><h2>Monitored Quality Indicators (ISO/IEC 25010)</h2>
<ul>
<li>Performance Efficiency - request latency, CPU/memory usage</li>
<li>Reliability - error rates, uptime</li>
<li>Functional Suitability - files processed by type and status</li>
<li>Usability - active users count</li>
</ul>
</div>
</body></html>''')

    def log_message(self, format, *args):
        pass


if __name__ == '__main__':
    sim_thread = threading.Thread(target=simulate_metrics, daemon=True)
    sim_thread.start()
    print("Starting metrics server on port 8000...")
    server = HTTPServer(('0.0.0.0', 8000), MetricsHandler)
    print("Metrics available at http://localhost:8000/metrics")
    server.serve_forever()
