# 8. Приложение. Настройка модели реализации качества с помощью выбранной системы мониторинга элементов показателей качества

## 8.1 Введение и выбор инструментов мониторинга

В качестве системы мониторинга элементов показателей качества выбран стек Prometheus + Grafana — промышленный стандарт для метрического мониторинга в микросервисных архитектурах.

**Prometheus** (версия 2.52.0) — система мониторинга с открытым исходным кодом, реализующая pull-модель сбора метрик. Сервер периодически обращается к эндпоинтам `/metrics` целевых приложений и сохраняет временные ряды в собственной базе данных TSDB. Поддерживает язык запросов PromQL для агрегации и анализа данных.

**Grafana** (версия 10.4.3) — платформа для визуализации данных мониторинга. Подключается к Prometheus как источнику данных и отображает метрики в виде интерактивных дашбордов с графиками, счётчиками и индикаторами.

Связь компонентов показателей качества по ГОСТ Р ИСО/МЭК 25010 с метриками системы мониторинга:

| Характеристика качества (25010) | Метрика Prometheus | Описание |
|---|---|---|
| Производительность (время отклика) | `app_request_duration_seconds` | Гистограмма задержек HTTP-запросов |
| Производительность (утилизация ресурсов) | `app_cpu_usage_percent`, `app_memory_usage_bytes` | Использование CPU и памяти |
| Надёжность (отказоустойчивость) | `app_errors_total` | Счётчик ошибок по типу |
| Функциональная пригодность | `app_files_processed_total` | Файлы, обработанные по типу и статусу |
| Практичность (используемость) | `app_active_users` | Количество активных пользователей |
| Производительность (пропускная способность) | `app_requests_total` | Общее число HTTP-запросов |

---

## 8.2 Архитектура развёрнутой системы мониторинга

```
┌─────────────────────────────────┐
│   Микросервис (app.py)          │
│   порт 8000                     │
│   GET /metrics → метрики в      │
│   формате Prometheus text       │
└──────────────┬──────────────────┘
               │  pull каждые 5 сек
               ▼
┌─────────────────────────────────┐
│   Prometheus 2.52.0             │
│   порт 9000                     │
│   TSDB, PromQL, UI              │
└──────────────┬──────────────────┘
               │  HTTP API запросы
               ▼
┌─────────────────────────────────┐
│   Grafana 10.4.3                │
│   порт 5000                     │
│   Дашборды, алерты, Explore     │
└─────────────────────────────────┘
```

Все три сервиса запускаются в рамках одной среды Replit через bash-скрипт `start_monitoring.sh`.

---

## 8.3 Программный код

### 8.3.1 Файл `app.py` — микросервис с метриками качества (новый файл)

Приложение реализует HTTP-сервер, который экспортирует показатели качества в формате Prometheus. Фоновый поток `simulate_metrics` непрерывно обновляет метрики, имитируя реальную работу микросервиса по обработке файлов.

```python
import time
import random
import threading
from http.server import HTTPServer, BaseHTTPRequestHandler
from prometheus_client import (
    Counter, Gauge, Histogram, Summary,
    generate_latest, CONTENT_TYPE_LATEST, CollectorRegistry, REGISTRY
)

# --- Объявление метрик ---

# Счётчик HTTP-запросов (характеристика: производительность)
REQUEST_COUNT = Counter(
    'app_requests_total',
    'Total number of HTTP requests',
    ['method', 'endpoint', 'status']
)

# Гистограмма задержек (характеристика: временное поведение, 25010 п. 8.4.1)
REQUEST_LATENCY = Histogram(
    'app_request_duration_seconds',
    'HTTP request latency in seconds',
    ['endpoint'],
    buckets=[0.01, 0.05, 0.1, 0.25, 0.5, 1.0, 2.0]
)

# Датчик активных пользователей (характеристика: практичность)
ACTIVE_USERS = Gauge(
    'app_active_users',
    'Number of currently active users'
)

# Счётчик обработанных файлов по типу (характеристика: функциональная пригодность)
FILES_PROCESSED = Counter(
    'app_files_processed_total',
    'Total files processed by type',
    ['file_type', 'status']
)

# Сводка времени обработки файлов
PROCESSING_TIME = Summary(
    'app_file_processing_seconds',
    'Time spent processing files',
    ['file_type']
)

# Счётчик ошибок (характеристика: надёжность, 25010 п. 8.5)
ERROR_COUNT = Counter(
    'app_errors_total',
    'Total number of application errors',
    ['error_type']
)

# Ресурсные метрики (характеристика: утилизация ресурсов, 25010 п. 8.4.3)
CPU_USAGE = Gauge('app_cpu_usage_percent', 'Simulated CPU usage percent')
MEMORY_USAGE = Gauge('app_memory_usage_bytes', 'Simulated memory usage in bytes')


def simulate_metrics():
    """Фоновый поток: непрерывно обновляет метрики качества."""
    file_types = ['json', 'csv', 'unknown', 'xml']
    endpoints = ['/process', '/health', '/upload', '/status']
    errors = ['timeout', 'format_error', 'validation_error']

    while True:
        # Обновляем ресурсные метрики
        ACTIVE_USERS.set(random.randint(5, 50))
        CPU_USAGE.set(random.uniform(10, 85))
        MEMORY_USAGE.set(random.uniform(50 * 1024 * 1024, 300 * 1024 * 1024))

        # Имитируем HTTP-трафик
        for ep in endpoints:
            REQUEST_COUNT.labels(method='GET', endpoint=ep, status='200').inc(
                random.randint(1, 10))
            REQUEST_LATENCY.labels(endpoint=ep).observe(
                random.uniform(0.01, 0.5))

        # Имитируем обработку файлов разных форматов
        for ft in file_types:
            FILES_PROCESSED.labels(file_type=ft, status='success').inc(
                random.randint(1, 20))
            # Неизвестные форматы обрабатываются дольше (ТЗ: < 2 сек)
            proc_time = (random.uniform(0.05, 2.0) if ft == 'unknown'
                         else random.uniform(0.01, 0.1))
            PROCESSING_TIME.labels(file_type=ft).observe(proc_time)

        # С вероятностью 30% генерируем ошибку
        if random.random() < 0.3:
            ERROR_COUNT.labels(error_type=random.choice(errors)).inc()
            REQUEST_COUNT.labels(
                method='POST', endpoint='/process', status='500').inc()

        time.sleep(3)


class MetricsHandler(BaseHTTPRequestHandler):
    """HTTP-обработчик: отдаёт метрики на GET /metrics."""

    def do_GET(self):
        if self.path == '/metrics':
            # Экспорт метрик в формате Prometheus text 0.0.4
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
            self.wfile.write(b'''<html>...страница приложения...</html>''')

    def log_message(self, format, *args):
        pass  # Отключаем стандартный лог запросов


if __name__ == '__main__':
    # Запуск фонового потока с генерацией метрик
    sim_thread = threading.Thread(target=simulate_metrics, daemon=True)
    sim_thread.start()
    print("Starting metrics server on port 8000...")
    server = HTTPServer(('0.0.0.0', 8000), MetricsHandler)
    print("Metrics available at http://localhost:8000/metrics")
    server.serve_forever()
```

---

### 8.3.2 Файл `prometheus.yml` — конфигурация Prometheus (новый файл)

Файл конфигурации задаёт глобальные параметры сбора метрик и два задания (`jobs`): самомониторинг Prometheus и сбор метрик с микросервиса.

```yaml
global:
  scrape_interval: 5s       # Период сбора метрик — каждые 5 секунд
  evaluation_interval: 5s   # Период вычисления правил алертинга

scrape_configs:
  # Job 1: самомониторинг Prometheus
  - job_name: 'prometheus'
    static_configs:
      - targets: ['localhost:9000']

  # Job 2: сбор метрик с микросервиса качества
  - job_name: 'quality-microservice'
    static_configs:
      - targets: ['localhost:8000']
    metrics_path: '/metrics'
    scrape_interval: 5s
```

---

### 8.3.3 Файл `grafana_config/grafana.ini` — конфигурация Grafana (новый файл)

Основной конфигурационный файл Grafana. Задаёт порт, пути хранения данных, учётные данные администратора и анонимный доступ в режиме просмотра.

```ini
[server]
http_port = 5000          ; Порт веб-интерфейса Grafana
domain = localhost

[paths]
data         = /home/runner/workspace/grafana_data
logs         = /home/runner/workspace/grafana_data/logs
plugins      = /home/runner/workspace/grafana_data/plugins
provisioning = /home/runner/workspace/grafana_config/provisioning

[security]
admin_user     = admin
admin_password = admin123

[auth.anonymous]
enabled  = true           ; Разрешён доступ без авторизации (режим просмотра)
org_name = Main Org.
org_role = Viewer

[log]
mode  = console
level = warn
```

---

### 8.3.4 Файл `grafana_config/provisioning/datasources/prometheus.yaml` — автоподключение Prometheus (новый файл)

Файл провижининга автоматически регистрирует Prometheus как источник данных при первом запуске Grafana, исключая ручную настройку через UI.

```yaml
apiVersion: 1

datasources:
  - name: Prometheus
    type: prometheus
    access: proxy             # Grafana обращается к Prometheus от своего имени
    url: http://localhost:9000
    isDefault: true           # Используется по умолчанию для всех дашбордов
    editable: true
    jsonData:
      timeInterval: "5s"      # Минимальный интервал обновления графиков
```

---

### 8.3.5 Файл `grafana_config/provisioning/dashboards/default.yaml` — провижининг дашбордов (новый файл)

Указывает Grafana, из какой директории автоматически загружать JSON-файлы дашбордов при запуске.

```yaml
apiVersion: 1

providers:
  - name: 'Quality Monitoring'
    orgId: 1
    folder: 'Quality'         # Папка в UI Grafana
    type: file
    disableDeletion: false
    editable: true
    options:
      path: /home/runner/workspace/grafana_config/dashboards
```

---

### 8.3.6 Файл `grafana_config/dashboards/quality_dashboard.json` — дашборд мониторинга качества (новый файл)

JSON-определение дашборда «Quality Monitoring — ISO/IEC 25010». Содержит 8 панелей, сгруппированных по характеристикам качества.

```json
{
  "title": "Quality Monitoring - ISO/IEC 25010",
  "tags": ["quality", "microservice"],
  "refresh": "5s",
  "time": { "from": "now-15m", "to": "now" },
  "panels": [
    {
      "id": 1,
      "title": "Active Users",
      "type": "stat",
      "gridPos": { "h": 4, "w": 6, "x": 0, "y": 0 },
      "targets": [{ "expr": "app_active_users" }],
      "fieldConfig": {
        "defaults": {
          "thresholds": {
            "steps": [
              {"color": "green",  "value": 0},
              {"color": "yellow", "value": 30},
              {"color": "red",    "value": 45}
            ]
          }
        }
      }
    },
    {
      "id": 2,
      "title": "CPU Usage (%)",
      "type": "gauge",
      "gridPos": { "h": 4, "w": 6, "x": 6, "y": 0 },
      "targets": [{ "expr": "app_cpu_usage_percent" }],
      "fieldConfig": {
        "defaults": {
          "min": 0, "max": 100, "unit": "percent",
          "thresholds": {
            "steps": [
              {"color": "green",  "value": 0},
              {"color": "yellow", "value": 60},
              {"color": "red",    "value": 80}
            ]
          }
        }
      }
    },
    {
      "id": 3,
      "title": "Memory Usage",
      "type": "stat",
      "gridPos": { "h": 4, "w": 6, "x": 12, "y": 0 },
      "targets": [{ "expr": "app_memory_usage_bytes" }],
      "fieldConfig": { "defaults": { "unit": "bytes" } }
    },
    {
      "id": 4,
      "title": "Total Requests",
      "type": "stat",
      "gridPos": { "h": 4, "w": 6, "x": 18, "y": 0 },
      "targets": [{ "expr": "sum(app_requests_total)" }]
    },
    {
      "id": 5,
      "title": "Request Rate (req/s)",
      "type": "timeseries",
      "gridPos": { "h": 8, "w": 12, "x": 0, "y": 4 },
      "targets": [{
        "expr": "rate(app_requests_total[1m])",
        "legendFormat": "{{endpoint}} {{status}}"
      }],
      "fieldConfig": { "defaults": { "unit": "reqps" } }
    },
    {
      "id": 6,
      "title": "Request Latency (p95)",
      "type": "timeseries",
      "gridPos": { "h": 8, "w": 12, "x": 12, "y": 4 },
      "targets": [{
        "expr": "histogram_quantile(0.95, rate(app_request_duration_seconds_bucket[2m]))",
        "legendFormat": "p95 {{endpoint}}"
      }],
      "fieldConfig": { "defaults": { "unit": "s" } }
    },
    {
      "id": 7,
      "title": "Files Processed by Type",
      "type": "timeseries",
      "gridPos": { "h": 8, "w": 12, "x": 0, "y": 12 },
      "targets": [{
        "expr": "rate(app_files_processed_total[1m])",
        "legendFormat": "{{file_type}} / {{status}}"
      }]
    },
    {
      "id": 8,
      "title": "Error Rate",
      "type": "timeseries",
      "gridPos": { "h": 8, "w": 12, "x": 12, "y": 12 },
      "targets": [{
        "expr": "rate(app_errors_total[1m])",
        "legendFormat": "{{error_type}}"
      }],
      "fieldConfig": {
        "defaults": { "color": { "mode": "fixed", "fixedColor": "red" } }
      }
    }
  ],
  "schemaVersion": 38
}
```

---

### 8.3.7 Файл `start_monitoring.sh` — скрипт запуска стека мониторинга (новый файл)

Bash-скрипт последовательно запускает все три компонента стека в фоновом режиме и ожидает готовности Grafana перед завершением инициализации.

```bash
#!/bin/bash
set -e

echo "=== Starting Quality Monitoring Stack ==="

# Установка Python-зависимостей
pip install prometheus_client -q 2>/dev/null || true

# --- Шаг 1: запуск микросервиса с метриками ---
echo "[1/3] Starting Python metrics app on port 8000..."
python app.py &
APP_PID=$!
sleep 2

# --- Шаг 2: запуск Prometheus ---
echo "[2/3] Starting Prometheus on port 9000..."
prometheus \
  --config.file=prometheus.yml \
  --storage.tsdb.path=prometheus_data \
  --web.listen-address=0.0.0.0:9000 \
  --log.level=warn &
PROM_PID=$!
sleep 3

# --- Шаг 3: запуск Grafana ---
echo "[3/3] Starting Grafana on port 5000..."
GRAFANA_HOME=$(dirname $(dirname $(which grafana-server)))/share/grafana
grafana server \
  --config=/home/runner/workspace/grafana_config/grafana.ini \
  --homepath=$GRAFANA_HOME &
GRAFANA_PID=$!

echo ""
echo "=== All services started ==="
echo "Metrics App : http://localhost:8000"
echo "Prometheus  : http://localhost:9000"
echo "Grafana     : http://localhost:5000  (admin / admin123)"
echo ""

# Ожидание готовности Grafana (опрос /api/health)
for i in $(seq 1 30); do
  if curl -s http://localhost:5000/api/health > /dev/null 2>&1; then
    echo "Grafana is ready!"
    break
  fi
  sleep 1
done

# Удерживаем все процессы запущенными
wait $APP_PID $PROM_PID $GRAFANA_PID
```

---

## 8.4 Процесс развёртывания

### Шаг 1. Установка системных зависимостей

Prometheus и Grafana устанавливаются через пакетный менеджер Nix, доступный в среде Replit:

```
Установлены пакеты: prometheus (2.52.0), grafana (10.4.3)
```

### Шаг 2. Создание структуры директорий

```
workspace/
├── app.py                                         # Микросервис с метриками
├── prometheus.yml                                 # Конфигурация Prometheus
├── start_monitoring.sh                            # Скрипт запуска стека
├── prometheus_data/                               # Хранилище TSDB (авто)
├── grafana_data/                                  # Данные Grafana (авто)
└── grafana_config/
    ├── grafana.ini                                # Основная конфигурация
    ├── provisioning/
    │   ├── datasources/
    │   │   └── prometheus.yaml                    # Автоподключение Prometheus
    │   └── dashboards/
    │       └── default.yaml                       # Автозагрузка дашбордов
    └── dashboards/
        └── quality_dashboard.json                 # Дашборд ISO/IEC 25010
```

### Шаг 3. Запуск стека

```bash
bash start_monitoring.sh
```

Вывод при успешном запуске:
```
=== Starting Quality Monitoring Stack ===
[1/3] Starting Python metrics app on port 8000...
[2/3] Starting Prometheus on port 9000...
[3/3] Starting Grafana on port 5000...
=== All services started ===
Metrics App : http://localhost:8000
Prometheus  : http://localhost:9000
Grafana     : http://localhost:5000  (admin / admin123)
Grafana is ready!
```

---

## 8.5 Настроенные показатели качества и их мониторинг

### Prometheus: PromQL-запросы для анализа качества

| Показатель качества | PromQL-запрос | Единица |
|---|---|---|
| Частота HTTP-запросов | `rate(app_requests_total[1m])` | req/s |
| 95-й перцентиль задержки | `histogram_quantile(0.95, rate(app_request_duration_seconds_bucket[2m]))` | сек |
| Частота ошибок | `rate(app_errors_total[1m])` | err/s |
| Активные пользователи | `app_active_users` | чел. |
| Нагрузка на CPU | `app_cpu_usage_percent` | % |
| Использование памяти | `app_memory_usage_bytes` | байт |
| Обработка файлов по типу | `rate(app_files_processed_total[1m])` | файл/s |

### Grafana: состав дашборда «Quality Monitoring — ISO/IEC 25010»

Дашборд содержит 8 панелей, организованных в две строки:

**Строка 1 — текущее состояние системы (stat/gauge):**
- Active Users — количество активных пользователей (цветовые пороги: зелёный до 30, жёлтый до 45, красный свыше 45)
- CPU Usage (%) — круговой индикатор с порогами 60% и 80%
- Memory Usage — текущее потребление памяти в байтах
- Total Requests — суммарное число запросов с момента запуска

**Строка 2 — временны́е ряды производительности:**
- Request Rate (req/s) — частота запросов по эндпоинтам
- Request Latency p95 — 95-й перцентиль времени ответа

**Строка 3 — временны́е ряды по функциональности и надёжности:**
- Files Processed by Type — скорость обработки файлов (json/csv/xml/unknown)
- Error Rate — частота ошибок по типу (timeout/format_error/validation_error)

---

## 8.6 Результаты развёртывания и верификация

По итогам развёртывания системы мониторинга получены следующие подтверждения работоспособности:

1. **Prometheus Targets** (скриншот 1): оба целевых сервиса отображаются со статусом **UP** — `prometheus (1/1 up)` и `quality-microservice (1/1 up)`. Задержка сбора метрик составляет 2–4 мс, что подтверждает низкие накладные расходы системы мониторинга.

2. **Prometheus Configuration** (скриншот 2): в веб-интерфейсе Prometheus отображается корректно применённая конфигурация с двумя job-ами и глобальным интервалом сбора 5 секунд.

3. **Prometheus Status** (скриншот 3): версия 2.52.0, дата запуска, статус перезагрузки конфигурации — **Successful**.

4. **Prometheus Query** (скриншот 4): PromQL-запрос `app_files_processed_total` возвращает 4 временных ряда с метками по типу файла (json, csv, xml, unknown), что соответствует функциональным требованиям ТЗ.

5. **Grafana Data Sources** (скриншоты 9–10): источник данных `Prometheus` зарегистрирован автоматически через провижининг, URL `http://localhost:9000`, статус — **default**.

6. **Grafana Dashboard** (скриншот 12): дашборд «Quality Monitoring — ISO/IEC 25010» отображает живые данные — 38 активных пользователей, загрузка CPU 57%, память 179 МиБ, 2735 суммарных запросов, графики частоты запросов, задержек p95, обработанных файлов и частоты ошибок.

7. **Grafana Explore** (скриншот 13): интерактивный запрос метрики `app_active_users` через Prometheus показывает временно́й ряд с характерными колебаниями от 5 до 50 пользователей, что соответствует логике фонового генератора метрик.

Таким образом, модель реализации качества программного средства полностью настроена: показатели качества по ГОСТ Р ИСО/МЭК 25010 (производительность, надёжность, функциональная пригодность, практичность) транслированы в измеримые метрики Prometheus, которые непрерывно собираются и визуализируются в Grafana с интервалом обновления 5 секунд.
