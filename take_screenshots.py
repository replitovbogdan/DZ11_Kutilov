import time
import os
from playwright.sync_api import sync_playwright

os.makedirs("screenshots", exist_ok=True)

GRAFANA = "http://localhost:5000"
PROMETHEUS = "http://localhost:9000"
APP = "http://localhost:8000"

def run(pw):
    browser = pw.chromium.launch(
        executable_path=os.environ.get("REPLIT_PLAYWRIGHT_CHROMIUM_EXECUTABLE"),
        args=["--no-sandbox", "--disable-setuid-sandbox"]
    )
    ctx = browser.new_context(viewport={"width": 1280, "height": 800})
    page = ctx.new_page()

    print("1. Prometheus: Targets page")
    page.goto(f"{PROMETHEUS}/targets")
    time.sleep(3)
    page.screenshot(path="screenshots/prometheus_targets.png", full_page=True)
    print("   Saved: prometheus_targets.png")

    print("2. Prometheus: Graph / Query page")
    page.goto(f"{PROMETHEUS}/graph?g0.expr=app_active_users&g0.tab=0")
    time.sleep(4)
    page.screenshot(path="screenshots/prometheus_graph.png", full_page=True)
    print("   Saved: prometheus_graph.png")

    print("3. Prometheus: Config page")
    page.goto(f"{PROMETHEUS}/config")
    time.sleep(2)
    page.screenshot(path="screenshots/prometheus_config.png", full_page=True)
    print("   Saved: prometheus_config.png")

    print("4. Metrics App: Main page")
    page.goto(APP)
    time.sleep(2)
    page.screenshot(path="screenshots/metrics_app.png", full_page=True)
    print("   Saved: metrics_app.png")

    print("5. Metrics App: /metrics endpoint")
    page.goto(f"{APP}/metrics")
    time.sleep(1)
    page.screenshot(path="screenshots/metrics_endpoint.png", full_page=True)
    print("   Saved: metrics_endpoint.png")

    print("6. Grafana: Login page")
    page.goto(f"{GRAFANA}/login")
    time.sleep(2)
    page.screenshot(path="screenshots/grafana_login_pw.png")
    print("   Saved: grafana_login_pw.png")

    print("7. Grafana: Login as admin")
    page.fill('input[name="user"]', "admin")
    page.fill('input[name="password"]', "admin123")
    page.click('button[type="submit"]')
    time.sleep(3)
    page.screenshot(path="screenshots/grafana_home_loggedin.png", full_page=True)
    print("   Saved: grafana_home_loggedin.png")

    print("8. Grafana: Datasources page")
    page.goto(f"{GRAFANA}/connections/datasources")
    time.sleep(3)
    page.screenshot(path="screenshots/grafana_datasources_list.png", full_page=True)
    print("   Saved: grafana_datasources_list.png")

    print("9. Grafana: Prometheus datasource details")
    page.goto(f"{GRAFANA}/connections/datasources/edit/PBFA97CFB590B2093")
    time.sleep(3)
    page.screenshot(path="screenshots/grafana_prometheus_datasource.png", full_page=True)
    print("   Saved: grafana_prometheus_datasource.png")

    print("10. Grafana: Dashboards list")
    page.goto(f"{GRAFANA}/dashboards")
    time.sleep(3)
    page.screenshot(path="screenshots/grafana_dashboards_list.png", full_page=True)
    print("   Saved: grafana_dashboards_list.png")

    print("11. Grafana: Explore with Prometheus query")
    page.goto(f"{GRAFANA}/explore?left=%7B%22datasource%22%3A%22Prometheus%22%2C%22queries%22%3A%5B%7B%22expr%22%3A%22app_active_users%22%2C%22refId%22%3A%22A%22%7D%5D%2C%22range%22%3A%7B%22from%22%3A%22now-15m%22%2C%22to%22%3A%22now%22%7D%7D")
    time.sleep(5)
    page.screenshot(path="screenshots/grafana_explore.png", full_page=True)
    print("   Saved: grafana_explore.png")

    print("12. Grafana: Alerting page")
    page.goto(f"{GRAFANA}/alerting/list")
    time.sleep(3)
    page.screenshot(path="screenshots/grafana_alerting.png", full_page=True)
    print("   Saved: grafana_alerting.png")

    browser.close()
    print("\nAll screenshots saved to ./screenshots/")

with sync_playwright() as pw:
    run(pw)
