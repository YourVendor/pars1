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
    # Здесь будет логика парсинга
    return soup

def extract_titles(soup):
    """Извлекает заголовки со страницы."""
    titles = soup.find_all('h1')  # Замени 'h1' на нужный тег
    return [title.text.strip() for title in titles]