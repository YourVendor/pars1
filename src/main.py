import sys
from pathlib import Path

# Добавляем корневую директорию проекта в sys.path
project_root = str(Path(__file__).resolve().parent.parent)
if project_root not in sys.path:
    sys.path.append(project_root)

from src.utils.helpers import fetch_page, parse_page, extract_product_info

def start_parsing(url):
    """Запускает парсинг для указанного URL."""
    print(f"Парсинг страницы: {url}")
    
    # Загружаем страницу
    html = fetch_page(url)
    if html:
        # Парсим страницу
        soup = parse_page(html)
        
        # Извлекаем информацию о продукте
        product_info = extract_product_info(soup)
        
        # Выводим результат
        print(f"Наименование: {product_info['name']}")
        print(f"Штрихкод: {product_info['barcode']}")
        print(f"Описание: {product_info['description']}")

if __name__ == "__main__":
    # Получаем URL из аргументов командной строки
    if len(sys.argv) > 1:
        url = sys.argv[1]
        start_parsing(url)
    else:
        print("Ошибка: URL не указан.")