import sys
from pathlib import Path

# Добавляем корневую директорию проекта в sys.path
project_root = str(Path(__file__).resolve().parent.parent)
if project_root not in sys.path:
    sys.path.append(project_root)

from src.utils.helpers import fetch_page, parse_page, extract_product_info, download_images

def start_parsing(url, identifier):
    """Запускает парсинг для указанного URL."""
    print(f"Парсинг страницы: {url}")
    
    try:
        # Загружаем страницу
        html = fetch_page(url)
        if not html:
            print("Ошибка: не удалось загрузить страницу.")
            return

        # Парсим страницу
        soup = parse_page(html)
        if not soup:
            print("Ошибка: не удалось распарсить страницу.")
            return
        
        # Извлекаем информацию о продукте
        product_info = extract_product_info(soup)
        if not product_info:
            print("Ошибка: не удалось извлечь информацию о продукте.")
            return
        
        # Выводим результат (только нужные данные)
        print(f"Наименование: {product_info['name']}")
        print(f"Штрихкод: {product_info['barcode']}")
        print(f"Описание: {product_info['description']}")

        # Скачиваем изображения
        base_path = str(Path(__file__).resolve().parent.parent)  # Корневая папка приложения
        download_images(soup, identifier, base_path)

    except Exception as e:
        print(f"Ошибка при парсинге: {e}")

if __name__ == "__main__":
    # Получаем URL и идентификатор из аргументов командной строки
    if len(sys.argv) > 2:
        url = sys.argv[1].strip('"')  # Убираем кавычки, если они есть
        identifier = sys.argv[2]
        start_parsing(url, identifier)
    else:
        print("Ошибка: URL и идентификатор не указаны.")