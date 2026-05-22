from django.shortcuts import render
from django.core.files.storage import default_storage
from django.core.files.base import ContentFile
from django.conf import settings
from .utils.processor import process_files, create_test_files, generate_charts
import base64
import os
import shutil
from django.views.decorators.csrf import csrf_exempt

@csrf_exempt  # Отключено для совместимости с Replit (лабораторная работа)
def index(request):
    results = None
    charts = {}

    # Создание тестовых файлов при первом запуске (если их нет)
    test_files = ['data.json', 'report.json', 'config.json', 'data.csv', 'backup.csv']
    test_files_exist = all(os.path.exists(f) for f in test_files)

    if not test_files_exist:
        create_test_files()
        print("Тестовые файлы созданы")

    # Обработка POST-запроса (загрузка файлов пользователем)
    if request.method == 'POST' and request.FILES.getlist('files'):
        print("=" * 50)
        print("ОБРАБОТКА POST-ЗАПРОСА (загрузка файлов пользователем)")
        print("=" * 50)

        uploaded_files = request.FILES.getlist('files')
        file_paths = []

        # Создаем директорию для загруженных файлов
        upload_dir = os.path.join(settings.BASE_DIR, 'uploads')
        os.makedirs(upload_dir, exist_ok=True)

        for uploaded_file in uploaded_files:
            # Сохраняем загруженный файл
            file_path = os.path.join(upload_dir, uploaded_file.name)

            # Проверяем, не существует ли уже файл с таким именем
            if os.path.exists(file_path):
                # Если существует, добавляем префикс
                name, ext = os.path.splitext(uploaded_file.name)
                counter = 1
                while os.path.exists(file_path):
                    new_name = f"{name}_{counter}{ext}"
                    file_path = os.path.join(upload_dir, new_name)
                    counter += 1

            # Сохраняем файл
            with open(file_path, 'wb') as dest:
                for chunk in uploaded_file.chunks():
                    dest.write(chunk)

            file_paths.append(file_path)
            print(f"Файл сохранен: {file_path}")

        # Обрабатываем загруженные файлы с помощью вашего микросервиса
        if file_paths:
            results = process_files(file_paths)
            print(f"Обработано файлов: {len(results)}")

            # Генерируем графики на основе результатов
            generate_charts(results)
            print("ПЕРВЫЙ ВЫЗОВ: графики после загрузки файлов пользователем")
            print("Файлы в директории:", os.listdir('.'))

            # Конвертируем сгенерированные графики в base64 для отображения в HTML
            chart_files = ['char7.png', 'char8.png', 'char9.png', 'char10.png']
            for chart_file in chart_files:
                if os.path.exists(chart_file):
                    with open(chart_file, 'rb') as img:
                        chart_name = chart_file.replace('.png', '')
                        charts[chart_name] = base64.b64encode(img.read()).decode()
                    print(f"✅ Загружен график: {chart_file}")
                else:
                    print(f"❌ График НЕ НАЙДЕН: {chart_file}")

    # Если нет POST-запроса, но есть тестовые файлы - обрабатываем их для демонстрации
    elif not results:
        print("=" * 50)
        print("ОБРАБОТКА ТЕСТОВЫХ ФАЙЛОВ (первый запуск)")
        print("=" * 50)

        test_file_paths = []
        for test_file in test_files:
            if os.path.exists(test_file):
                test_file_paths.append(os.path.abspath(test_file))
                print(f"Тестовый файл найден: {test_file}")

        if test_file_paths:
            results = process_files(test_file_paths)
            print(f"Обработано тестовых файлов: {len(results)}")

            generate_charts(results)
            print("ВТОРОЙ ВЫЗОВ: графики после обработки тестовых файлов")
            print("Файлы в директории:", os.listdir('.'))

            # Конвертируем графики в base64
            chart_files = ['char7.png', 'char8.png', 'char9.png', 'char10.png']
            for chart_file in chart_files:
                if os.path.exists(chart_file):
                    with open(chart_file, 'rb') as img:
                        chart_name = chart_file.replace('.png', '')
                        charts[chart_name] = base64.b64encode(img.read()).decode()
                    print(f"✅ Загружен график: {chart_file}")
                else:
                    print(f"❌ График НЕ НАЙДЕН: {chart_file}")
        else:
            print("Тестовые файлы не найдены!")

    # Ваша фамилия и инициалы
    full_name = "Кутилов Б.А."

    print(f"Передаем в шаблон: results={results is not None}, charts={len(charts)} графиков")
    print("=" * 50)

    context = {
        'results': results,
        'charts': charts,
        'full_name': full_name,
    }

    return render(request, 'tasks//index.html', context)


def clean_uploads(request):
    """
    Дополнительная функция для очистки загруженных файлов (по желанию)
    Можно добавить URL для вызова этой функции
    """
    if request.method == 'POST':
        upload_dir = os.path.join(settings.BASE_DIR, 'uploads')
        if os.path.exists(upload_dir):
            shutil.rmtree(upload_dir)
            os.makedirs(upload_dir, exist_ok=True)

        # Также удаляем сгенерированные графики
        chart_files = ['char7.png', 'char8.png', 'char9.png', 'char10.png']
        for chart_file in chart_files:
            if os.path.exists(chart_file):
                os.remove(chart_file)

    return index(request)