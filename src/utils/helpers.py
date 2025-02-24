import requests
from bs4 import BeautifulSoup
import time
import random

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
            "Referer": "https://www.informat.ru/",  # Добавляем Referer
            "Sec-Fetch-Dest": "document",
            "Sec-Fetch-Mode": "navigate",
            "Sec-Fetch-Site": "same-origin",
            "Sec-Fetch-User": "?1",
            "Upgrade-Insecure-Requests": "1",
        }

        # Куки (если нужны)
        cookies = {
            "session_id": "1234567890abcdef",  # Пример куки
        }

        # Выполняем запрос с автоматическим следованием за переадресацией
        response = requests.get(
            url,
            headers=headers,
            cookies=cookies,
            timeout=10,
            allow_redirects=True
        )
        response.raise_for_status()  # Проверяем статус ответа

        # Возвращаем финальный URL и HTML
        print(f"Финальный URL после переадресации: {response.url}")
        return response.text
    except requests.exceptions.RequestException as e:
        print(f"Ошибка при загрузке страницы: {e}")
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
        product_info['description'] = description_tag.text.strip()
    else:
        product_info['description'] = "N/A"

    return product_info