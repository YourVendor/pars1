import requests
from bs4 import BeautifulSoup
import time
import random
import os
from PIL import Image
from io import BytesIO

def fetch_page(url):
    delay = random.uniform(3, 7)  # Задержка 3-7 секунд
    time.sleep(delay)
    user_agents = [
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.114 Safari/537.36",
        "Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:89.0) Gecko/20100101 Firefox/89.0",
        "Mozilla/5.0 (iPhone; CPU iPhone OS 14_6 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.1.1 Mobile/15E148 Safari/604.1",
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:89.0) Gecko/20100101 Firefox/89.0"
    ]
    headers = {
        "User-Agent": random.choice(user_agents),
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8",
        "Accept-Language": "ru-RU,ru;q=0.9,en-US;q=0.8,en;q=0.7",
        "Accept-Encoding": "gzip, deflate, br",
        "Connection": "keep-alive",
        "Referer": "https://www.informat.ru/",
        "Cookie": f"PHPSESSID={random.randint(1000, 9999)}; user_region=RU",  # Динамические cookies
        "Upgrade-Insecure-Requests": "1",
    }
    try:
        response = requests.get(url, headers=headers, timeout=30, allow_redirects=True)  # Таймаут 30 секунд
        response.raise_for_status()
        return response.text
    except requests.RequestException as e:
        print(f"Ошибка загрузки {url}: {e}")
        return None

def parse_page(html):
    return BeautifulSoup(html, 'html.parser') if html else None

def extract_product_info(soup, config):
    if not soup:
        return {}
    
    product_info = {}
    for tag, attr, role, sibling in config:
        try:
            if "=" in attr:
                attr_key, attr_value = attr.split("=", 1)
                if attr_key == "text":
                    tag_elem = soup.find(tag, text=attr_value)
                    if tag_elem:
                        for sib in sibling.split(","):
                            next_elem = tag_elem.find_next_sibling(sib.strip())
                            if next_elem:
                                product_info[role] = next_elem.get_text(separator=" ", strip=True)
                                break
                        else:
                            product_info[role] = tag_elem.get_text(separator=" ", strip=True)
                    else:
                        product_info[role] = "N/A"
                else:
                    tag_elem = soup.find(tag, {attr_key: attr_value})
                    product_info[role] = tag_elem.get_text(separator=" ", strip=True) if tag_elem else "N/A"
            else:
                tag_elem = soup.find(tag, id=attr) if attr.startswith("id=") else soup.find(tag)
                product_info[role] = tag_elem.get_text(separator=" ", strip=True) if tag_elem else "N/A"
        except Exception as e:
            product_info[role] = f"Ошибка: {e}"
    return product_info

def download_images(soup, identifier, base_url, output_folder, image_container):
    if not soup:
        return []

    try:
        tag, attr_str = image_container.split(",", 1)
        attr_key, attr_value = attr_str.split("=", 1)
        container_attrs = {attr_key.strip(): attr_value.strip()}
    except ValueError:
        tag = image_container
        container_attrs = {}

    image_container_elem = soup.find(tag, **container_attrs)
    if not image_container_elem:
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

            if not main_image_set:
                filename = f"{identifier}.jpg"
                main_image_set = True
            else:
                filename = f"{identifier}a.jpg"
            
            file_path = os.path.join(output_folder, filename)
            with open(file_path, 'wb') as file:
                file.write(response.content)
            saved_images.append(file_path)

            if len(saved_images) == 2:
                break

        except Exception:
            continue

    return saved_images