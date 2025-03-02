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
import os  # Убедимся, что импорт тут

def log_message(log_widget, message):
    log_widget.insert(tk.END, f"[{time.strftime('%H:%M:%S')}] {message}\n")
    log_widget.see(tk.END)

def load_file():
    file_path = filedialog.askopenfilename(
        title="Выберите файл содержащий Тег, Атрибут, Роль, Тег для поиска",
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
    config_win.title("Настройка тегов (макс. 30)")
    config_win.geometry("700x450")

    tk.Label(config_win, text="Тег").grid(row=0, column=0, padx=5, pady=5)
    tk.Label(config_win, text="Атрибут").grid(row=0, column=1, padx=5, pady=5)
    tk.Label(config_win, text="Роль").grid(row=0, column=2, padx=5, pady=5)
    tk.Label(config_win, text="Тег для поиска (Идущий следующим)").grid(row=0, column=3, padx=5, pady=5)

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
            with open("config.json", "w") as f:
                json.dump({"tags": config, "image_container": image_container}, f)
        config_win.destroy()

    def load_config_from_file():
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
                    tag_entry, attr_entry, role_entry, sibling_entry = tags[i]
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
    tk.Button(config_win, text="Загрузить из файла", command=load_config_from_file).grid(row=32, column=1, padx=5, pady=10)

    config_win.wait_window()

    default_config = {
        "tags": [
            ("h1", "itemprop=name", "name", "dd"),
            ("dt", "text=Штрихкод:", "barcode", "dd"),
            ("div", "id=tab1", "description", "dd")
        ],
        "image_container": "div, class_=item-slider-holder"
    }
    if Path("config.json").exists():
        with open("config.json", "r") as f:
            config_data = json.load(f)
            return config_data["tags"], config_data.get("image_container", default_config["image_container"])
    return default_config["tags"], default_config["image_container"]

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

def start_parsing(log_widget, progress_bar, root):
    df = load_file()
    if df is None or df.empty:
        log_message(log_widget, "Файл не загружен или пуст.")
        messagebox.showerror("Ошибка", "Файл не загружен или пуст.")
        return
    if len(df.columns) < 3:
        log_message(log_widget, "Файл должен содержать как минимум 3 колонки: ID, URL, Base URL.")
        messagebox.showerror("Ошибка", "Файл должен содержать как минимум 3 колонки.")
        return

    output_folder = select_output_folder()
    if not output_folder:
        log_message(log_widget, "Папка для сохранения не выбрана.")
        messagebox.showerror("Ошибка", "Папка для сохранения не выбрана.")
        return

    config, image_container = configure_tags()
    result_queue = queue.Queue()
    threads = []
    total_urls = len([row for _, row in df.iterrows() if not pd.isna(row.iloc[1]) and row.iloc[1].startswith("http")])
    completed = 0

    for index, row in df.iterrows():
        identifier, url, base_url = str(row.iloc[0]), row.iloc[1], row.iloc[2]
        if pd.isna(url) or not url.startswith("http"):
            log_message(log_widget, f"Пропуск строки {index + 1}: некорректная ссылка.")
            continue
        if pd.isna(base_url) or not base_url.startswith("http"):
            log_message(log_widget, f"Пропуск строки {index + 1}: некорректный Base URL.")
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
            progress_bar['value'] = (completed / total_urls) * 100
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

    log_widget = scrolledtext.ScrolledText(root, width=90, height=25)
    log_widget.pack(pady=10)

    progress_bar = ttk.Progressbar(root, length=400, mode='determinate')
    progress_bar.pack(pady=10)

    tk.Button(root, text="ПАРС", command=lambda: start_parsing(log_widget, progress_bar, root)).pack(pady=10)

    root.mainloop()

if __name__ == "__main__":
    create_interface()