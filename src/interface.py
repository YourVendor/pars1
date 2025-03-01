import tkinter as tk
from tkinter import filedialog, messagebox, scrolledtext
import pandas as pd
from src.utils.helpers import fetch_page, parse_page, extract_product_info, download_images
import json
import time
import random
from pathlib import Path

def log_message(log_widget, message):
    """Логирует сообщение в текстовое поле с временной меткой."""
    log_widget.insert(tk.END, f"[{time.strftime('%H:%M:%S')}] {message}\n")
    log_widget.see(tk.END)

def load_file():
    """Загружает XLSX-файл."""
    file_path = filedialog.askopenfilename(
        title="Выберите файл",
        filetypes=(("Excel files", "*.xlsx"), ("All files", "*.*"))
    )
    if file_path:
        try:
            df = pd.read_excel(file_path)
            return df
        except Exception as e:
            return None
    return None

def configure_tags():
    """Открывает окно для настройки тегов (до 30 полей)."""
    config_win = tk.Toplevel()
    config_win.title("Настройка тегов (макс. 30)")
    config_win.geometry("600x400")

    # Поля ввода
    tk.Label(config_win, text="Тег").grid(row=0, column=0, padx=5, pady=5)
    tk.Label(config_win, text="Атрибут (например, itemprop=name)").grid(row=0, column=1, padx=5, pady=5)
    tk.Label(config_win, text="Роль (имя поля)").grid(row=0, column=2, padx=5, pady=5)

    tags = []
    for i in range(30):
        tag_entry = tk.Entry(config_win, width=15)
        attr_entry = tk.Entry(config_win, width=20)
        role_entry = tk.Entry(config_win, width=15)
        tag_entry.grid(row=i+1, column=0, padx=5, pady=2)
        attr_entry.grid(row=i+1, column=1, padx=5, pady=2)
        role_entry.grid(row=i+1, column=2, padx=5, pady=2)
        tags.append((tag_entry, attr_entry, role_entry))

    def save_config():
        config = [(t.get(), a.get(), r.get()) for t, a, r in tags if t.get() and r.get()]
        if config:
            with open("config.json", "w") as f:
                json.dump(config, f)
        config_win.destroy()

    tk.Button(config_win, text="Сохранить", command=save_config).grid(row=31, column=0, columnspan=3, pady=10)
    config_win.wait_window()

    return json.load(open("config.json")) if Path("config.json").exists() else [
        ("h1", "itemprop=name", "name"),
        ("dt", "text=Штрихкод:", "barcode"),
        ("div", "id=tab1", "description")
    ]

def start_parsing(log_widget):
    """Запускает парсинг для всех ссылок из файла."""
    df = load_file()
    if df is None or df.empty:
        log_message(log_widget, "Файл не загружен или пуст.")
        messagebox.showerror("Ошибка", "Файл не загружен или пуст.")
        return
    if len(df.columns) < 2:
        log_message(log_widget, "Файл должен содержать как минимум 2 колонки: ID и URL.")
        messagebox.showerror("Ошибка", "Файл должен содержать как минимум 2 колонки.")
        return

    config = configure_tags()
    results = []
    base_path = str(Path(__file__).resolve().parent.parent)

    for index, row in df.iterrows():
        identifier, url = str(row[0]), row[1]
        if pd.isna(url) or not url.startswith("http"):
            log_message(log_widget, f"Пропуск строки {index + 1}: некорректная ссылка.")
            continue

        log_message(log_widget, f"Парсинг страницы: {url}")
        html = fetch_page(url)
        if not html:
            log_message(log_widget, f"Не удалось загрузить страницу: {url}")
            results.append([identifier, url] + ["Ошибка"] * len(config))
            continue

        soup = parse_page(html)
        product_info = extract_product_info(soup, config)
        images = download_images(soup, identifier, base_path)

        log_message(log_widget, f"Извлечено: {json.dumps(product_info, ensure_ascii=False)}")
        log_message(log_widget, f"Скачаны изображения: {images}")
        results.append([identifier, url] + [product_info.get(role, "N/A") for _, _, role in config])

        delay = random.randint(3, 8)
        log_message(log_widget, f"Ожидание {delay} секунд...")
        time.sleep(delay)

    output_df = pd.DataFrame(results, columns=["Идентификатор", "Ссылка"] + [role for _, _, role in config])
    output_path = base_path + "/Готовый парс.xlsx"
    output_df.to_excel(output_path, index=False)
    log_message(log_widget, f"Результаты сохранены в {output_path}")
    messagebox.showinfo("Готово", f"Парсинг завершён. Результаты в {output_path}")

def create_interface():
    """Создаёт графический интерфейс."""
    root = tk.Tk()
    root.title("Парсер")
    root.geometry("800x600")

    log_widget = scrolledtext.ScrolledText(root, width=90, height=30)
    log_widget.pack(pady=10)

    tk.Button(root, text="ПАРС", command=lambda: start_parsing(log_widget)).pack(pady=10)

    root.mainloop()

if __name__ == "__main__":
    create_interface()