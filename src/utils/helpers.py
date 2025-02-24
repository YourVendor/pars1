import requests
from bs4 import BeautifulSoup

def fetch_page(url):
    """Загружает HTML-страницу по указанному URL."""
    try:
        response = requests.get(url, timeout=10)  # Таймаут 10 секунд
        response.raise_for_status()  # Проверяем статус ответа
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
        product_info['name'] = None

    # Извлекаем штрихкод
    barcode_tag = soup.find('dt', text='Штрихкод:')
    if barcode_tag:
        barcode_value = barcode_tag.find_next_sibling('dd')
        if barcode_value:
            product_info['barcode'] = barcode_value.text.strip()
        else:
            product_info['barcode'] = None
    else:
        product_info['barcode'] = None

    # Извлекаем описание
    description_tag = soup.find('div', id='tab1', itemprop='description')
    if description_tag:
        product_info['description'] = description_tag.text.strip()
    else:
        product_info['description'] = None

    return product_info