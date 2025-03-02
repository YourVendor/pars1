import tkinter as tk
from tkinter import filedialog, messagebox, scrolledtext, ttk
import pandas as pd
from src.utils.helpers import fetch_page, parse_page, extract_product_info, download_images
import json
import time
import random
from pathlib import Path
import threading
import queue
import os
import re
import asyncio
import aiohttp

def log_message(log_widget, message):
    log_widget.insert(tk.END, f"[{time.strftime('%H:%M:%S')}] {message}\n")
    log_widget.see(tk.END)

def load_file():
    file_path = filedialog.askopenfilename(
        title="Выберите файл (pred_data.xlsx)",
        filetypes=(("Excel files", "*.xlsx"), ("All files", "*.*"))
    )
    if file_path:
        try:
            df = pd.read_excel(file_path)
            return df
        except Exception:
            return None
    return None

def configure_tags():
    config_win = tk.Toplevel()
    config_win.title("Настройка парсинга (макс. 30)")
    config_win.geometry("700x450")

    tk.Label(config_win, text="Тег").grid(row=0, column=0, padx=5, pady=5)
    tk.Label(config_win, text="Атрибут").grid(row=0, column=1, padx=5, pady=5)
    tk.Label(config_win, text="Роль").grid(row=0, column=2, padx=5, pady=5)
    tk.Label(config_win, text="Тег для поиска").grid(row=0, column=3, padx=5, pady=5)

    tags = []
    for i in range(30):
        tag_entry = tk.Entry(config_win, width=15)
        attr_entry = tk.Entry(config_win, width=20)
        role_entry = tk.Entry(config_win, width=15)
        sibling_entry = tk.Entry(config_win, width=15)
        tag_entry.grid(row=i+1, column=0, padx=5, pady=2)
        attr_entry.grid(row=i+1, column=1, padx=5, pady=2)
        role_entry.grid(row=i+1, column=2, padx=5, pady=2)
        sibling_entry.grid(row=i+1, column=3, padx=5, pady=2)
        tags.append((tag_entry, attr_entry, role_entry, sibling_entry))

    tk.Label(config_win, text="Контейнер картинок (тег, класс)").grid(row=31, column=0, columnspan=2, padx=5, pady=5)
    image_container_entry = tk.Entry(config_win, width=35)
    image_container_entry.grid(row=31, column=2, columnspan=2, padx=5, pady=5)
    image_container_entry.insert(0, "div, class_=item-slider-holder")

    def save_config():
        config = [(t.get(), a.get(), r.get(), s.get() or "dd") for t, a, r, s in tags if t.get() and r.get()]
        image_container = image_container_entry.get()
        if config:
            with open("parse_config.json", "w") as f:
                json.dump({"tags": config, "image_container": image_container}, f)
        config_win.destroy()

    def load_config_from_file(tags_entries):
        file_path = filedialog.askopenfilename(
            title="Выберите файл с настройками",
            filetypes=(("Excel files", "*.xlsx"), ("All files", "*.*"))
        )
        if file_path:
            try:
                df = pd.read_excel(file_path)
                required_columns = ["Тег", "Атрибут", "Роль", "Тег для поиска"]
                if not all(col in df.columns for col in required_columns):
                    messagebox.showerror("Ошибка", "Файл должен содержать колонки: Тег, Атрибут, Роль, Тег для поиска")
                    return
                
                for i, row in df.iterrows():
                    if i >= 30:
                        break
                    tag_entry, attr_entry, role_entry, sibling_entry = tags_entries[i]
                    tag_entry.delete(0, tk.END)
                    attr_entry.delete(0, tk.END)
                    role_entry.delete(0, tk.END)
                    sibling_entry.delete(0, tk.END)
                    tag_entry.insert(0, str(row["Тег"]))
                    attr_entry.insert(0, str(row["Атрибут"]))
                    role_entry.insert(0, str(row["Роль"]))
                    sibling_entry.insert(0, str(row["Тег для поиска"]) if pd.notna(row["Тег для поиска"]) else "dd")
            except Exception as e:
                messagebox.showerror("Ошибка", f"Не удалось загрузить файл: {e}")

    tk.Button(config_win, text="Сохранить", command=save_config).grid(row=32, column=0, padx=5, pady=10)
    tk.Button(config_win, text="Загрузить из файла", command=lambda: load_config_from_file(tags)).grid(row=32, column=1, padx=5, pady=10)

    config_win.wait_window()

    default_config = {
        "tags": [
            ("h1", "itemprop=name", "name", "dd"),
            ("dt", "text=Штрихкод:", "barcode", "dd"),
            ("div", "id=tab1", "description", "dd")
        ],
        "image_container": "div, class_=item-slider-holder"
    }
    if Path("parse_config.json").exists():
        with open("parse_config.json", "r") as f:
            config_data = json.load(f)
            return (
                config_data["tags"],
                config_data.get("image_container", default_config["image_container"])
            )
    return default_config["tags"], default_config["image_container"]

def configure_link_collection():
    config_win = tk.Toplevel()
    config_win.title("Настройка сбора ссылок")
    config_win.geometry("400x200")

    tk.Label(config_win, text="Контейнер товаров (тег, класс)").grid(row=0, column=0, padx=5, pady=5)
    link_container_entry = tk.Entry(config_win, width=35)
    link_container_entry.grid(row=0, column=1, padx=5, pady=5)
    link_container_entry.insert(0, "div, class_=item-box")

    def save_config():
        link_container = link_container_entry.get()
        with open("link_config.json", "w") as f:
            json.dump({"link_container": link_container}, f)
        config_win.destroy()

    tk.Button(config_win, text="Сохранить", command=save_config).grid(row=1, column=0, columnspan=2, pady=10)

    config_win.wait_window()

    default_config = {"link_container": "div, class_=item-box"}
    if Path("link_config.json").exists():
        with open("link_config.json", "r") as f:
            config_data = json.load(f)
            return config_data.get("link_container", default_config["link_container"])
    return default_config["link_container"]

def select_output_folder():
    folder = filedialog.askdirectory(title="Выберите папку для сохранения результатов")
    return folder if folder else None

def parse_url(identifier, url, config, image_container, base_url, output_folder, result_queue, log_widget):
    log_message(log_widget, f"Парсинг страницы: {url}")
    html = fetch_page(url)
    if not html:
        log_message(log_widget, f"Не удалось загрузить страницу: {url}")
        result_queue.put([identifier, url] + ["Ошибка"] * len(config))
        return

    soup = parse_page(html)
    product_info = extract_product_info(soup, config)
    images = download_images(soup, identifier, base_url, output_folder, image_container)

    log_message(log_widget, f"Извлечено: {json.dumps(product_info, ensure_ascii=False)}")
    log_message(log_widget, f"Скачаны изображения: {images}")
    result_queue.put([identifier, url] + [product_info.get(role, "N/A") for _, _, role, _ in config])

async def fetch_page_async(url, session):
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
    }
    try:
        await asyncio.sleep(random.uniform(1, 3))  # Задержка
        async with session.get(url, headers=headers, timeout=aiohttp.ClientTimeout(total=10)) as response:
            response.raise_for_status()
            return await response.text()
    except Exception:
        return None

def collect_links(base_url, log_widget, progress_bar, root):
    if not base_url or not base_url.startswith("http"):
        log_message(log_widget, "Некорректный базовый URL.")
        messagebox.showerror("Ошибка", "Введите корректный базовый URL.")
        return

    output_folder = select_output_folder()
    if not output_folder:
        log_message(log_widget, "Папка для сохранения не выбрана.")
        messagebox.showerror("Ошибка", "Папка для сохранения не выбрана.")
        return

    link_container = configure_link_collection()
    log_message(log_widget, f"Сбор ссылок с {base_url} (контейнер: {link_container})")

    async def gather_links_recursive(url, collected_links, visited_urls, depth=0, max_depth=3):
        if depth > max_depth or url in visited_urls:
            return
        visited_urls.add(url)
        log_message(log_widget, f"Сканируем страницу: {url} (глубина {depth})")

        async with aiohttp.ClientSession() as session:
            html = await fetch_page_async(url, session)
            if not html:
                log_message(log_widget, f"Не удалось загрузить страницу: {url}")
                return

            soup = parse_page(html)
            base_path = "https://www.informat.ru"
            group_prefix = base_url.replace(base_path, '')  # Например, /catalog/ofisnye-tovary/bumaga-dlya-ofisnoy-tekhniki/

            # Ищем товары в контейнерах
            try:
                tag, attr_str = link_container.split(",", 1)
                attr_key, attr_value = attr_str.split("=", 1)
                container_attrs = {attr_key.strip(): attr_value.strip()}
                item_boxes = soup.find_all(tag, **container_attrs)
                for elem in item_boxes:
                    a_tag = elem.find('a', href=True)
                    if a_tag:
                        href = a_tag['href']
                        if href:
                            if href.startswith('/'):
                                href = base_path + href
                            if href.startswith('http'):
                                href = href.replace('https://www.informat.ru/catalog/catalog', 'https://www.informat.ru/catalog')
                                if ('/brands/' not in href and 
                                    re.search(r'_[\w\d]{5,}$', href) and 
                                    group_prefix in href and 
                                    '/filter/' not in href and 
                                    '?' not in href):
                                    collected_links.append(href)
                                    log_message(log_widget, f"Найдена ссылка на товар (в контейнере): {href}")
            except ValueError:
                log_message(log_widget, f"Некорректный формат контейнера '{link_container}'.")

            # Ищем подкатегории и товары среди всех ссылок
            log_message(log_widget, f"Ищем подкатегории и товары на {url}")
            for a_tag in soup.find_all('a', href=True):
                href = a_tag['href']
                if href.startswith('/'):
                    href = base_path + href
                if href.startswith('http') and group_prefix in href and '/brands/' not in href and '/filter/' not in href and '?' not in href:
                    if re.search(r'_[\w\d]{5,}$', href):  # Сначала проверяем, товар ли это
                        if href not in collected_links:
                            collected_links.append(href)
                            log_message(log_widget, f"Найдена ссылка на товар: {href}")
                    elif href not in visited_urls:  # Если не товар — подкатегория
                        log_message(log_widget, f"Найдена подкатегория: {href}")
                        await gather_links_recursive(href, collected_links, visited_urls, depth + 1, max_depth)
                elif href.startswith('http') and group_prefix in href and ('/filter/' in href or '?' in href):
                    log_message(log_widget, f"Отброшена ссылка с фильтром/сортировкой: {href}")

    def run_collection():
        links = []
        visited_urls = set()
        asyncio.run(gather_links_recursive(base_url, links, visited_urls))

        if not links:
            log_message(log_widget, "Не найдено ни одной ссылки на товары после обхода страниц.")
        else:
            log_message(log_widget, f"Найдено {len(links)} ссылок на товары.")
            process_links(links, output_folder, log_widget, progress_bar, root)

    threading.Thread(target=run_collection, daemon=True).start()

def process_links(links, output_folder, log_widget, progress_bar, root):
    log_message(log_widget, f"Обрабатываем {len(links)} ссылок.")

    result_queue = queue.Queue()
    threads = []
    total_links = len(links)
    completed = 0
    collected_so_far = 0

    def parse_link(link):
        nonlocal collected_so_far
        link_html = fetch_page(link)
        if not link_html:
            result_queue.put([link, "Ошибка"])
            log_message(log_widget, f"Ошибка загрузки {link}")
            return
        link_soup = parse_page(link_html)
        text = link_soup.get_text()
        barcodes = re.findall(r'\b\d{13}\b', text)
        result_queue.put([link] + barcodes)
        collected_so_far += 1
        log_message(log_widget, f"Собрано: {collected_so_far}/{total_links} (ссылка: {link})")

    for link in links:
        thread = threading.Thread(target=parse_link, args=(link,))
        threads.append(thread)
        thread.start()

    def update_progress():
        nonlocal completed
        for thread in threads:
            thread.join()

        results = []
        while not result_queue.empty():
            result = result_queue.get()
            results.append(result)
            completed += 1
            progress_bar['value'] = (completed / total_links) * 100 if total_links > 0 else 100
            root.update_idletasks()

        if results:
            max_barcodes = max(len(row) - 1 for row in results)
            columns = ["URL"] + [f"barcode{i+1}" if i > 0 else "barcode" for i in range(max_barcodes)]
            output_df = pd.DataFrame(results, columns=columns[:max(len(row) for row in results)])
        else:
            output_df = pd.DataFrame(columns=["URL"])

        output_path = os.path.join(output_folder, "pred_data.xlsx")
        output_df.to_excel(output_path, index=False)
        log_message(log_widget, f"Ссылки и штрихкоды сохранены в {output_path}")
        messagebox.showinfo("Готово", f"Сбор завершён. Результаты в {output_path}")

    threading.Thread(target=update_progress, daemon=True).start()

def start_parsing(log_widget, progress_bar, root):
    df = load_file()
    if df is None or df.empty:
        log_message(log_widget, "Файл не загружен или пуст.")
        messagebox.showerror("Ошибка", "Файл не загружен или пуст.")
        return
    if len(df.columns) < 2:  # URL и barcode
        log_message(log_widget, "Файл должен содержать как минимум 2 колонки: URL и barcode.")
        messagebox.showerror("Ошибка", "Файл должен содержать как минимум 2 колонки.")
        return

    output_folder = select_output_folder()
    if not output_folder:
        log_message(log_widget, "Папка для сохранения не выбрана.")
        messagebox.showerror("Ошибка", "Папка для сохранения не выбрана.")
        return

    config, image_container = configure_tags()
    result_queue = queue.Queue()
    threads = []
    total_urls = len([row for _, row in df.iterrows() if not pd.isna(row.iloc[0]) and row.iloc[0].startswith("http")])
    completed = 0

    for index, row in df.iterrows():
        url = row.iloc[0]  # URL в первой колонке
        identifier = str(row.iloc[1]) if len(df.columns) > 1 and pd.notna(row.iloc[1]) else f"item_{index}"  # Barcode или индекс
        base_url = url.rsplit('/', 1)[0]  # Берем Base URL из самой ссылки
        if pd.isna(url) or not url.startswith("http"):
            log_message(log_widget, f"Пропуск строки {index + 1}: некорректная ссылка.")
            continue

        thread = threading.Thread(target=parse_url, args=(identifier, url, config, image_container, base_url, output_folder, result_queue, log_widget))
        threads.append(thread)
        thread.start()

    def update_progress():
        nonlocal completed
        for thread in threads:
            thread.join()

        results = []
        while not result_queue.empty():
            results.append(result_queue.get())
            completed += 1
            progress_bar['value'] = (completed / total_urls) * 100 if total_urls > 0 else 100
            root.update_idletasks()

        output_df = pd.DataFrame(results, columns=["Идентификатор", "Ссылка"] + [role for _, _, role, _ in config])
        output_path = os.path.join(output_folder, "Готовый парс.xlsx")
        output_df.to_excel(output_path, index=False)
        log_message(log_widget, f"Результаты сохранены в {output_path}")
        messagebox.showinfo("Готово", f"Парсинг завершён. Результаты в {output_path}")

    threading.Thread(target=update_progress, daemon=True).start()

def create_interface():
    root = tk.Tk()
    root.title("Парсер")
    root.geometry("800x600")

    log_widget = scrolledtext.ScrolledText(root, width=90, height=20)
    log_widget.pack(pady=10)

    progress_bar = ttk.Progressbar(root, length=400, mode='determinate')
    progress_bar.pack(pady=10)

    tk.Button(root, text="ПАРС", command=lambda: start_parsing(log_widget, progress_bar, root)).pack(pady=5)

    tk.Label(root, text="Базовый URL для сбора ссылок:").pack(pady=5)
    base_url_entry = tk.Entry(root, width=50)
    base_url_entry.pack(pady=5)

    tk.Button(root, text="Собрать ссылки", command=lambda: collect_links(base_url_entry.get(), log_widget, progress_bar, root)).pack(pady=5)

    root.mainloop()

if __name__ == "__main__":
    create_interface()