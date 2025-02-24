from src.utils.helpers import fetch_page, parse_page, extract_titles
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
        
        # Извлекаем заголовки
        titles = extract_titles(soup)
        print("Найденные заголовки:")
        for title in titles:
            print(title)