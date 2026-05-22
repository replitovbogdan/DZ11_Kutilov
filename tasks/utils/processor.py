import pandas as pd
import json
import os
from datetime import datetime
import matplotlib.pyplot as plt
import numpy as np
from django.conf import settings

# Настройка шрифтов для графиков
plt.rcParams['font.family'] = ['DejaVu Sans']
plt.rcParams['axes.unicode_minus'] = False

class DataStorage:
    def __init__(self):
        self.processed_files = []

    def load_file(self, filename):
        file_info = {
            "filename": filename,
            "format": "unknown",
            "load_time": 0,
            "error": "",
            "status": ""
        }

        start_time = datetime.now()

        try:
            if not os.path.exists(filename):
                raise FileNotFoundError("File not found")

            if filename.endswith('.json'):
                f = open(filename, 'r')
                data = json.load(f)
                f.close()
                file_info["format"] = "JSON"
                file_info["status"] = "success"

            elif filename.endswith('.csv'):
                data = pd.read_csv(filename)
                file_info["format"] = "CSV"
                file_info["status"] = "success"

            else:
                raise ValueError("Unknown format")

        except Exception as e:
            file_info["status"] = "failed"
            file_info["error"] = str(e)
            data = {"file": filename, "status": "reserve data"}

        end_time = datetime.now()
        file_info["load_time"] = (end_time - start_time).total_seconds()

        self.processed_files.append(file_info)
        return data

    def get_results(self):
        return self.processed_files

def create_test_files():
    """Создание тестовых файлов для демонстрации работы"""
    print("СОЗДАНИЕ ТЕСТОВЫХ ФАЙЛОВ")

    json_data1 = {"name": "Test Data", "values": [6, 2, 3, 4, 5]}
    f = open('data.json', 'w')
    json.dump(json_data1, f)
    f.close()
    print("  Создан: data.json")

    json_data2 = {"reports": ["report1", "report2", "report3"]}
    f = open('report.json', 'w')
    json.dump(json_data2, f)
    f.close()
    print("  Создан: report.json")

    json_data3 = {"config": {"debug": True, "timeout": 30}}
    f = open('config.json', 'w')
    json.dump(json_data3, f)
    f.close()
    print("  Создан: config.json")

    csv_data1 = pd.DataFrame({
        'Name': ['Alice', 'Bob', 'Charlie'],
        'Age': [25, 30, 35]
    })
    csv_data1.to_csv('data.csv', index=False)
    print("  Создан: data.csv")

    csv_data2 = pd.DataFrame({
        'Date': pd.date_range('2024-01-01', periods=5),
        'Value': np.random.randn(5)
    })
    csv_data2.to_csv('backup.csv', index=False)
    print("  Создан: backup.csv")

    print("\nВсе тестовые файлы успешно созданы!")

def process_files(file_list):
    """Обработка списка файлов"""
    storage = DataStorage()

    print("\nФайлы для обработки:")
    for f in file_list:
        print("  - " + f)

    for file in file_list:
        storage.load_file(file)

    return storage.get_results()

def generate_charts(results):
    """Генерация графиков на основе результатов обработки"""
    # График 1: Статусы (char7.png)
    success_count = 0
    failed_count = 0
    for result in results:
        if result['status'] == 'success':
            success_count += 1
        else:
            failed_count += 1

    fig, ax = plt.subplots()
    ax.pie([success_count, failed_count], labels=None, autopct=None, shadow=True,
           wedgeprops={'lw': 1, 'ls': '--', 'edgecolor': "k"})
    ax.axis("equal")
    plt.title('Распределение статусов загрузки файлов', fontsize=12, fontweight='bold')
    plt.savefig('char7.png', dpi=100, bbox_inches='tight')
    plt.close()

    # График 2: Время загрузки (char8.png)
    filenames = []
    load_times = []
    colors = []
    for result in results:
        filenames.append(result['filename'])
        load_times.append(result['load_time'])
        if result['status'] == 'success':
            colors.append('green')
        else:
            colors.append('red')

    plt.figure(figsize=(12, 6))
    plt.bar(filenames, load_times, color=colors, edgecolor='black')
    plt.xlabel('Название файла', fontsize=12)
    plt.ylabel('Время загрузки (секунды)', fontsize=12)
    plt.title('Время загрузки по файлам', fontsize=14, fontweight='bold')
    plt.xticks(rotation=45, ha='right')
    plt.tight_layout()
    plt.savefig('char8.png', dpi=100, bbox_inches='tight')
    plt.close()

    # График 3: Сравнение успешных/неудачных (char9.png)
    fig, ax = plt.subplots()
    ax.pie([success_count, failed_count], labels=None, autopct=None, shadow=True,
           wedgeprops={'lw': 1, 'ls': '--', 'edgecolor': "k"})
    ax.axis("equal")
    plt.title('Сравнение успешных и неудачных загрузок', fontsize=12, fontweight='bold')
    plt.savefig('char9.png', dpi=100, bbox_inches='tight')
    plt.close()

    # График 4: Среднее время по форматам (char10.png)
    json_times = []
    csv_times = []
    for result in results:
        if result['status'] == 'success':
            if result['format'] == 'JSON':
                json_times.append(result['load_time'])
            elif result['format'] == 'CSV':
                csv_times.append(result['load_time'])

    formats = []
    avg_times = []

    if json_times:
        formats.append('JSON')
        avg_times.append(sum(json_times) / len(json_times))

    if csv_times:
        formats.append('CSV')
        avg_times.append(sum(csv_times) / len(csv_times))

    if formats:
        plt.figure(figsize=(8, 6))
        plt.bar(formats, avg_times, color='skyblue', edgecolor='black')
        plt.xlabel('Формат файла', fontsize=12)
        plt.ylabel('Среднее время загрузки (секунды)', fontsize=12)
        plt.title('Среднее время загрузки по форматам файлов', fontsize=14, fontweight='bold')
        plt.tight_layout()
        plt.savefig('char10.png', dpi=100, bbox_inches='tight')
        plt.close()

def show_results(results):
    """Вывод результатов в консоль (для отладки)"""
    print("ТАБЛИЧНОЕ ПРЕДСТАВЛЕНИЕ")
    print(f"{'Название файла':<20} {'Время загрузки (сек)':<20} {'Статус':<10} {'Ошибка':<30}")
    for result in results:
        filename = result['filename']
        load_time = f"{result['load_time']:.3f}"
        status = result['status'].upper()
        error = result['error'] if result['error'] else "-"
        print(f"{filename:<20} {load_time:<20} {status:<10} {error:<30}")
    print("ВИЗУАЛИЗАЦИЯ")
def generate_charts(results):
  """Генерация всех графиков на основе результатов"""
  # Код из вашей функции show_results(), но без print
  # (полный код я дал в предыдущем ответе на Шаг 3)
def generate_charts(results):
    """Генерация всех графиков на основе результатов"""
    # График 1: Статусы (char7.png)
    success_count = 0
    failed_count = 0
    for result in results:
        if result['status'] == 'success':
            success_count += 1
        else:
            failed_count += 1

    fig, ax = plt.subplots()
    ax.pie([success_count, failed_count], labels=None, autopct=None, shadow=True,
           wedgeprops={'lw': 1, 'ls': '--', 'edgecolor': "k"})
    ax.axis("equal")
    plt.title('Распределение статусов загрузки файлов', fontsize=12, fontweight='bold')
    plt.savefig('char7.png', dpi=100, bbox_inches='tight')
    plt.close()

    # График 2: Время загрузки (char8.png)
    filenames = []
    load_times = []
    colors = []
    for result in results:
        filenames.append(result['filename'])
        load_times.append(result['load_time'])
        if result['status'] == 'success':
            colors.append('green')
        else:
            colors.append('red')

    plt.figure(figsize=(12, 6))
    plt.bar(filenames, load_times, color=colors, edgecolor='black')
    plt.xlabel('Название файла', fontsize=12)
    plt.ylabel('Время загрузки (секунды)', fontsize=12)
    plt.title('Время загрузки по файлам', fontsize=14, fontweight='bold')
    plt.xticks(rotation=45, ha='right')
    plt.tight_layout()
    plt.savefig('char8.png', dpi=100, bbox_inches='tight')
    plt.close()

    # График 3: Сравнение успешных/неудачных (char9.png)
    fig, ax = plt.subplots()
    ax.pie([success_count, failed_count], labels=None, autopct=None, shadow=True,
           wedgeprops={'lw': 1, 'ls': '--', 'edgecolor': "k"})
    ax.axis("equal")
    plt.title('Сравнение успешных и неудачных загрузок', fontsize=12, fontweight='bold')
    plt.savefig('char9.png', dpi=100, bbox_inches='tight')
    plt.close()

    # График 4: Среднее время по форматам (char10.png)
    json_times = []
    csv_times = []
    for result in results:
        if result['status'] == 'success':
            if result['format'] == 'JSON':
                json_times.append(result['load_time'])
            elif result['format'] == 'CSV':
                csv_times.append(result['load_time'])

    formats = []
    avg_times = []

    if json_times:
        formats.append('JSON')
        avg_times.append(sum(json_times) / len(json_times))

    if csv_times:
        formats.append('CSV')
        avg_times.append(sum(csv_times) / len(csv_times))

    if formats:
        plt.figure(figsize=(8, 6))
        plt.bar(formats, avg_times, color='skyblue', edgecolor='black')
        plt.xlabel('Формат файла', fontsize=12)
        plt.ylabel('Среднее время загрузки (секунды)', fontsize=12)
        plt.title('Среднее время загрузки по форматам файлов', fontsize=14, fontweight='bold')
        plt.tight_layout()
        plt.savefig('char10.png', dpi=100, bbox_inches='tight')
        plt.close()

    print("Графики сохранены: char7.png, char8.png, char9.png, char10.png")