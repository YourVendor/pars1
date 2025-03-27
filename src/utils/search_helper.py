import requests
import random
import time
from bs4 import BeautifulSoup
import os
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time

def fetch_search_page(query, log_file="search_log.txt", retries=3):
    url = f"https://www.wildberries.ru/catalog/0/search.aspx?search={query}"
    options = Options()
    options.add_argument("--headless")
    options.add_argument("--disable-gpu")
    options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/134.0.6998.178 Safari/537.36")
    
    driver = None
    attempt = 0
    while attempt < retries:
        try:
            driver = webdriver.Chrome(options=options)
            driver.set_page_load_timeout(60)  # Таймаут загрузки страницы
            driver.get(url)
            WebDriverWait(driver, 60).until(  # Увеличим до 60 сек
                EC.presence_of_element_located((By.CLASS_NAME, "searching-results__count"))
            )
            html = driver.page_source
            with open(log_file, "a", encoding="utf-8") as f:
                f.write(f"[{time.strftime('%H:%M:%S')}] Запрос: {query}\nURL: {driver.current_url}\nHTML:\n{html[:2000]}\n---\n")
            return html
        except Exception as e:
            attempt += 1
            with open(log_file, "a", encoding="utf-8") as f:
                f.write(f"[{time.strftime('%H:%M:%S')}] Ошибка для {query} (попытка {attempt}/{retries}): {e}\n")
            if driver:
                driver.quit()
            time.sleep(5)  # Пауза перед повтором
        finally:
            if driver:
                driver.quit()
    return None

def get_item_count(html):
    from bs4 import BeautifulSoup
    soup = BeautifulSoup(html, 'html.parser')
    count_tag = soup.find("span", class_="searching-results__count")
    return count_tag.text.strip() if count_tag else "N/A"

def get_item_count(html):
    if not html:
        return "Ошибка"
    soup = BeautifulSoup(html, 'html.parser')
    count_elem = soup.find("span", class_="searching-results__count")
    if count_elem:
        inner_span = count_elem.find("span")
        return inner_span.text.strip() if inner_span else "N/A"
    return "N/A"