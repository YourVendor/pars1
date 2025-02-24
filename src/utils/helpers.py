import requests
from bs4 import BeautifulSoup
import time
import random
import os
from PIL import Image  # Для работы с изображениями
from io import BytesIO  # Для загрузки изображений в память

def fetch_page(url):
    """Загружает HTML-страницу по указанному URL, следуя за переадресацией."""
    try:
        # Случайная задержка перед запросом (от 1 до 3 секунд)
        delay = random.uniform(1, 3)
        time.sleep(delay)

        # Заголовки для имитации реального браузера
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8",
            "Accept-Language": "ru-RU,ru;q=0.9,en-US;q=0.8,en;q=0.7",
            "Accept-Encoding": "gzip, deflate, br",
            "Connection": "keep-alive",
            "Referer": "https://www.informat.ru/",
            "Sec-Fetch-Dest": "document",
            "Sec-Fetch-Mode": "navigate",
            "Sec-Fetch-Site": "same-origin",
            "Sec-Fetch-User": "?1",
            "Upgrade-Insecure-Requests": "1",
        }

        # Выполняем запрос с автоматическим следованием за переадресацией
        response = requests.get(url, headers=headers, timeout=10, allow_redirects=True)
        response.raise_for_status()  # Проверяем статус ответа

        # Возвращаем финальный URL и HTML
        print(f"Финальный URL после переадресации: {response.url}")
        return response.text
    except requests.exceptions.HTTPError as e:
        print(f"Ошибка HTTP при загрузке страницы {url}: {e}")
        return None
    except requests.exceptions.RequestException as e:
        print(f"Ошибка при загрузке страницы {url}: {e}")
        return None

def parse_page(html):
    """Парсит HTML-страницу и извлекает данные."""
    soup = BeautifulSoup(html, 'html.parser')
    return soup

def extract_product_info(soup):
    """Извлекает информацию о продукте: название, штрихкод и описание."""
    product_info = {}

    # Извлекаем название
    name_tag = soup.find('h1', itemprop='name')
    if name_tag:
        product_info['name'] = name_tag.text.strip()
    else:
        product_info['name'] = "N/A"

    # Извлекаем штрихкод
    barcode_tag = soup.find('dt', text='Штрихкод:')
    if barcode_tag:
        barcode_value = barcode_tag.find_next_sibling('dd')
        if barcode_value:
            product_info['barcode'] = barcode_value.text.strip()
        else:
            product_info['barcode'] = "N/A"
    else:
        product_info['barcode'] = "N/A"

    # Извлекаем описание
    description_tag = soup.find('div', id='tab1', itemprop='description')
    if description_tag:
        # Убираем все HTML-теги из описания
        description_text = description_tag.get_text(separator=" ", strip=True)
        product_info['description'] = description_text
    else:
        product_info['description'] = "N/A"

    return product_info

def download_images(soup, identifier, base_path):
    """Скачивает изображения и сохраняет их в указанную папку, игнорируя слишком маленькие."""
    # Базовый URL сайта
    base_url = "https://www.informat.ru"

    # Находим контейнер с изображениями
    image_container = soup.find('div', class_='item-slider-holder')
    if not image_container:
        print("Контейнер с изображениями не найден.")
        return []

    # Находим все изображения внутри контейнера
    images = image_container.find_all('img')
    if not images:
        print("Изображения не найдены.")
        return []

    # Создаём папку для сохранения изображений, если её нет
    os.makedirs(base_path, exist_ok=True)

    saved_images = []
    for i, img in enumerate(images):
        # Получаем URL изображения
        img_url = img.get('src')
        if not img_url:
            continue

        # Если URL относительный, добавляем базовый URL
        if img_url.startswith('/'):
            img_url = base_url + img_url

        # Скачиваем изображение для проверки размера
        try:
            response = requests.get(img_url, stream=True)
            response.raise_for_status()

            # Загружаем изображение в память
            img_data = BytesIO(response.content)
            img_pil = Image.open(img_data)

            # Проверяем размер изображения
            width, height = img_pil.size
            if width < 110 or height < 110:  # Игнорируем изображения меньше 110x110 пикселей
                print(f"Изображение {img_url} слишком маленькое ({width}x{height}), пропускаем.")
                continue

            # Формируем имя файла
            if i == 0:
                filename = f"{identifier}.jpg"
            else:
                filename = f"{identifier}a.jpg"

            # Полный путь для сохранения
            file_path = os.path.join(base_path, filename)

            # Сохраняем изображение
            with open(file_path, 'wb') as file:
                file.write(response.content)
            print(f"Изображение сохранено: {file_path} ({width}x{height})")
            saved_images.append(file_path)

        except Exception as e:
            print(f"Ошибка при скачивании изображения {img_url}: {e}")

    return saved_images