import requests
from bs4 import BeautifulSoup
import time
import random
import os
from PIL import Image
from io import BytesIO

def fetch_page(url):
    """Загружает HTML-страницу по URL с переадресацией."""
    delay = random.uniform(1, 3)
    time.sleep(delay)
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8",
        "Accept-Language": "ru-RU,ru;q=0.9,en-US;q=0.8,en;q=0.7",
        "Accept-Encoding": "gzip, deflate, br",
        "Connection": "keep-alive",
        "Referer": "https://www.google.com/",
        "Sec-Fetch-Dest": "document",
        "Sec-Fetch-Mode": "navigate",
        "Sec-Fetch-Site": "cross-site",
        "Sec-Fetch-User": "?1",
        "Upgrade-Insecure-Requests": "1",
    }
    try:
        response = requests.get(url, headers=headers, timeout=10, allow_redirects=True)
        response.raise_for_status()
        return response.text
    except requests.RequestException:
        return None

def parse_page(html):
    """Парсит HTML в BeautifulSoup."""
    return BeautifulSoup(html, 'html.parser') if html else None

def extract_product_info(soup, config):
    """Извлекает данные по пользовательским тегам из config."""
    if not soup:
        return {}
    
    product_info = {}
    for tag, attr, role in config:
        try:
            # Разбираем атрибут: "itemprop=name" -> {"itemprop": "name"}, "text=Штрихкод:" -> текст внутри тега
            if "=" in attr:
                attr_key, attr_value = attr.split("=", 1)
                if attr_key == "text":
                    # Ищем тег с точным текстом
                    tag_elem = soup.find(tag, text=attr_value)
                    if tag_elem:
                        for sib in sibling.split(","):  # Поддержка нескольких тегов через запятую
                            next_elem = tag_elem.find_next_sibling(sib.strip())
                            if next_elem:
                                product_info[role] = next_elem.get_text(separator=" ", strip=True)
                                break
                        else:
                            product_info[role] = tag_elem.get_text(separator=" ", strip=True)
                    else:
                        product_info[role] = "N/A"
                else:
                    # Ищем по атрибуту
                    tag_elem = soup.find(tag, {attr_key: attr_value})
                    product_info[role] = tag_elem.get_text(separator=" ", strip=True) if tag_elem else "N/A"
            else:
                # Простой тег без атрибутов
                tag_elem = soup.find(tag, id=attr) if attr.startswith("id=") else soup.find(tag)
                product_info[role] = tag_elem.get_text(separator=" ", strip=True) if tag_elem else "N/A"
        except Exception as e:
            product_info[role] = f"Ошибка: {e}"
    return product_info

def download_images(soup, identifier, base_path):
    if not soup:
        return []

    base_url = "https://www.informat.ru"  # Пока оставим, до следующей итерации
    image_container = soup.find('div', class_='item-slider-holder')
    if not image_container:
        return []

    images = image_container_elem.find_all('img')
    if not images:
        return []

    os.makedirs(output_folder, exist_ok=True)
    saved_images = []
    main_image_set = False

    for img in images:
        img_url = img.get('src')
        if not img_url:
            continue
        if img_url.startswith('/'):
            img_url = base_url.rstrip('/') + img_url

        try:
            response = requests.get(img_url, stream=True)
            response.raise_for_status()
            img_data = BytesIO(response.content)
            img_pil = Image.open(img_data)
            width, height = img_pil.size

            if width < 110 or height < 110:
                continue

            # Первое подходящее — основное, второе — дополнительное
            if not main_image_set:
                filename = f"{identifier}.jpg"
                main_image_set = True
            else:
                filename = f"{identifier}a.jpg"
            
            file_path = os.path.join(output_folder, filename)
            with open(file_path, 'wb') as file:
                file.write(response.content)
            saved_images.append(file_path)

            if len(saved_images) == 2:  # Хватит двух
                break

        except Exception:
            continue

    return saved_images
