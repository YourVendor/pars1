import sys
from pathlib import Path

# Добавляем корневую директорию проекта в sys.path
project_root = str(Path(__file__).resolve().parent.parent)
if project_root not in sys.path:
    sys.path.append(project_root)

from src.utils.helpers import fetch_page, parse_page, extract_product_info
from config import PARSING_URL

def start_parsing():
    print("Парсер запущен!")
    
    # Используем URL из конфигурации
    url = PARSING_URL
    
    # Загружаем страницу
    html = fetch_page(url)
    if html:
        # Парсим страницу
        soup = parse_page(html)
        
        # Извлекаем информацию о продукте
        product_info = extract_product_info(soup)
        
        # Выводим результат
        print("Найденная информация о продукте:")
        print(f"Наименование: {product_info['name']}")
        print(f"Штрихкод: {product_info['barcode']}")
        print(f"Описание: {product_info['description']}")

if __name__ == "__main__":
    start_parsing()