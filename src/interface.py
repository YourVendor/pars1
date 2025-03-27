import tkinter as tk
from concurrent.futures import ThreadPoolExecutor
from tkinter import filedialog, messagebox, scrolledtext, ttk, Toplevel, Label, Canvas
import pandas as pd
from src.utils.helpers import fetch_page, parse_page, extract_product_info, download_images
from src.utils.search_helper import fetch_search_page, get_item_count
import json
import time
import random
from pathlib import Path
import threading
import queue
import os
import webbrowser

class App:
    def __init__(self, root):
        self.root = root
        self.root.title("Парсер и Анализ")
        self.root.geometry("800x600")
        self.root.iconbitmap("parser.ico")

        # Очередь для логов
        self.log_queue = queue.Queue()

        # Вкладки
        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(pady=10, expand=True)

        # Вкладка 1: Парсер карточек
        self.tab1 = ttk.Frame(self.notebook)
        self.notebook.add(self.tab1, text="Парсер карточек")
        self.log_widget1 = scrolledtext.ScrolledText(self.tab1, width=90, height=25)
        self.log_widget1.pack(pady=10)
        tk.Button(self.tab1, text="ПАРС", command=self.start_parsing_thread).pack(pady=10)

        # Вкладка 2: Анализ запросов
        self.tab2 = ttk.Frame(self.notebook)
        self.notebook.add(self.tab2, text="Анализ запросов")
        self.log_widget2 = scrolledtext.ScrolledText(self.tab2, width=90, height=25)
        self.log_widget2.pack(pady=10)

        # Выбор максимального числа итераций при нуле
        self.max_retries_frame = tk.Frame(self.tab2)
        self.max_retries_frame.pack(pady=5)
        tk.Label(self.max_retries_frame, text="Сколько раз байтим нули:").pack(side=tk.LEFT)
        self.max_retries_var = tk.IntVar(value=3)
        tk.Spinbox(self.max_retries_frame, from_=1, to=10, width=5, textvariable=self.max_retries_var).pack(side=tk.LEFT, padx=5)

        # Выбор количества одновременно запущенных Chrome
        self.chrome_count_frame = tk.Frame(self.tab2)
        self.chrome_count_frame.pack(pady=5)
        tk.Label(self.chrome_count_frame, text="Сколько Chrome одновременно:").pack(side=tk.LEFT)
        self.chrome_count_var = tk.IntVar(value=2)  # По умолчанию 2
        tk.Spinbox(self.chrome_count_frame, from_=1, to=10, width=5, textvariable=self.chrome_count_var).pack(side=tk.LEFT, padx=5)

        tk.Button(self.tab2, text="АНАЛИЗ", command=self.start_analysis_thread).pack(pady=10)

        # Обновление логов
        self.update_logs()

    def log(self, widget, message):
        """Добавляем сообщение в очередь логов"""
        self.log_queue.put((widget, f"[{time.strftime('%H:%M:%S')}] {message}"))

    def update_logs(self):
        """Обновляем текстовое поле логов из очереди"""
        while not self.log_queue.empty():
            widget, message = self.log_queue.get()
            widget.insert(tk.END, message + "\n")
            widget.see(tk.END)
        self.root.after(100, self.update_logs)

    # === Парсер карточек ===
    def load_file_parser(self):
        file_path = filedialog.askopenfilename(
            title="Выберите файл содержащий ID, url на позицию, базовый url",
            filetypes=(("Excel files", "*.xlsx"), ("All files", "*.*"))
        )
        if file_path:
            try:
                df = pd.read_excel(file_path)
                return df
            except Exception:
                return None
        return None

    def configure_tags(self):
        config_win = Toplevel(self.root)
        config_win.title("Настройка тегов (макс. 30)")
        config_win.geometry("700x450")
        config_win.iconbitmap("parser.ico")

        canvas = Canvas(config_win)
        scrollbar = ttk.Scrollbar(config_win, orient="vertical", command=canvas.yview)
        scrollable_frame = tk.Frame(canvas)

        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)

        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        tk.Label(scrollable_frame, text="Тег").grid(row=0, column=0, padx=5, pady=5)
        tk.Label(scrollable_frame, text="Атрибут").grid(row=0, column=1, padx=5, pady=5)
        tk.Label(scrollable_frame, text="Роль").grid(row=0, column=2, padx=5, pady=5)
        tk.Label(scrollable_frame, text="Тег для поиска (Идущий следующим)").grid(row=0, column=3, padx=5, pady=5)

        tags = []
        for i in range(30):
            tag_entry = tk.Entry(scrollable_frame, width=15)
            attr_entry = tk.Entry(scrollable_frame, width=20)
            role_entry = tk.Entry(scrollable_frame, width=15)
            sibling_entry = tk.Entry(scrollable_frame, width=15)
            tag_entry.grid(row=i+1, column=0, padx=5, pady=2)
            attr_entry.grid(row=i+1, column=1, padx=5, pady=2)
            role_entry.grid(row=i+1, column=2, padx=5, pady=2)
            sibling_entry.grid(row=i+1, column=3, padx=5, pady=2)
            tags.append((tag_entry, attr_entry, role_entry, sibling_entry))

        tk.Label(scrollable_frame, text="Контейнер картинок (тег, класс)").grid(row=31, column=0, columnspan=2, padx=5, pady=5)
        image_container_entry = tk.Entry(scrollable_frame, width=35)
        image_container_entry.grid(row=31, column=2, columnspan=2, padx=5, pady=5)
        image_container_entry.insert(0, "div, class_=catalog_detail detail element_1")

        def save_config():
            config = [(t.get(), a.get(), r.get(), s.get() or "dd") for t, a, r, s in tags if t.get() and r.get()]
            image_container = image_container_entry.get()
            if config:
                with open("config.json", "w") as f:
                    json.dump({"tags": config, "image_container": image_container}, f)
            config_win.destroy()

        def load_config_from_file():
            file_path = filedialog.askopenfilename(
                title="Выберите файл с Тегом, атрибутами, ролями и тегами для поиска",
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

        tk.Button(scrollable_frame, text="Сохранить", command=save_config).grid(row=32, column=0, padx=5, pady=10)
        tk.Button(scrollable_frame, text="Загрузить из файла", command=load_config_from_file).grid(row=32, column=1, padx=5, pady=10)

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

    def select_output_folder(self):
        folder = filedialog.askdirectory(title="Выберите папку для сохранения результатов")
        return folder if folder else None

    def load_poems(self):
        poems_file = "poems.txt"
        poems = []
        if os.path.exists(poems_file):
            try:
                with open(poems_file, "r", encoding="utf-8") as f:
                    content = f.read()
            except UnicodeDecodeError:
                with open(poems_file, "r", encoding="windows-1251") as f:
                    content = f.read()
            content = content.encode().decode('utf-8', errors='replace')
            for line in content.splitlines():
                if "|" in line:
                    title, poem = line.strip().split("|", 1)
                    poem = poem.replace(r'\n', '\n')
                    poems.append((title, poem))
        return poems

    def show_poem(self, completed, total_urls):
        poems = self.load_poems()
        if not poems:
            self.log(self.log_widget1, "Не удалось загрузить стихи из poems.txt")
            return
        
        if total_urls < 50 or completed < 50 or (completed % 500 != 0 and completed != total_urls):
            return

        poem_win = Toplevel(self.root)
        poem_win.title("Стих для души")
        poem_win.geometry("400x300")
        poem_win.transient(self.root)
        poem_win.grab_set()
        poem_win.iconbitmap("parser.ico")

        title, poem = random.choice(poems)
        tk.Label(poem_win, text=title, font=("Arial", 14, "bold")).pack(pady=5)

        poem_frame = tk.Frame(poem_win)
        poem_frame.pack(pady=5)
        scrollbar = tk.Scrollbar(poem_frame, orient="vertical")
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        poem_text = tk.Text(poem_frame, height=8, width=40, font=("Arial", 12), wrap="word", yscrollcommand=scrollbar.set)
        poem_text.insert(tk.END, poem)
        poem_text.config(state="disabled")
        poem_text.pack(side=tk.LEFT)
        scrollbar.config(command=poem_text.yview)

        link_frame = tk.Frame(poem_win)
        link_frame.pack(pady=5)
        link_label = tk.Label(link_frame, text="Познакомиться с Наблюдателем", font=("Arial", 10, "underline"), fg="blue", cursor="hand2")
        link_label.pack()
        link_label.bind("<Button-1>", lambda e: webbrowser.open("https://t.me/watcher_of_universe"))

        def close_poem():
            poem_win.destroy()

        tk.Button(poem_win, text="Закрыть", command=close_poem).pack(pady=5)
        poem_win.after(5000, close_poem)

    def parse_url(self, identifier, url, config, image_container, base_url, output_folder, result_queue):
        self.log(self.log_widget1, f"Парсинг страницы: {url}")
        for attempt in range(3):
            html = fetch_page(url)
            if html:
                break
            self.log(self.log_widget1, f"Попытка {attempt + 1} не удалась для {url}")
            time.sleep(5)
        else:
            self.log(self.log_widget1, f"Не удалось загрузить страницу после 3 попыток: {url}")
            result_queue.put([identifier, url] + ["Ошибка"] * len(config))
            return

        soup = parse_page(html)
        product_info = extract_product_info(soup, config)
        images = download_images(soup, identifier, base_url, output_folder, image_container)

        self.log(self.log_widget1, f"Извлечено: {json.dumps(product_info, ensure_ascii=False)}")
        self.log(self.log_widget1, f"Скачаны изображения: {images}")
        result_queue.put([identifier, url] + [product_info.get(role, "N/A") for _, _, role, _ in config])

    def start_parsing_thread(self):
        thread = threading.Thread(target=self.start_parsing)
        thread.start()

    def start_parsing(self):
        df = self.load_file_parser()
        if df is None or df.empty:
            self.log(self.log_widget1, "Файл не загружен или пуст.")
            messagebox.showerror("Ошибка", "Файл не загружен или пуст.")
            return
        if len(df.columns) < 3:
            self.log(self.log_widget1, "Файл должен содержать как минимум 3 колонки: ID, URL, Base URL.")
            messagebox.showerror("Ошибка", "Файл должен содержать как минимум 3 колонки.")
            return

        output_folder = self.select_output_folder()
        if not output_folder:
            self.log(self.log_widget1, "Папка для сохранения не выбрана.")
            messagebox.showerror("Ошибка", "Папка для сохранения не выбрана.")
            return

        config, image_container = self.configure_tags()
        result_queue = queue.Queue()
        threads = []
        total_urls = len([row for _, row in df.iterrows() if not pd.isna(row.iloc[1]) and row.iloc[1].startswith("http")])
        completed = 0

        for index, row in df.iterrows():
            identifier, url, base_url = str(row.iloc[0]), row.iloc[1], row.iloc[2]
            if pd.isna(url) or not url.startswith("http"):
                self.log(self.log_widget1, f"Пропуск строки {index + 1}: некорректная ссылка.")
                continue
            if pd.isna(base_url) or not base_url.startswith("http"):
                self.log(self.log_widget1, f"Пропуск строки {index + 1}: некорректный Base URL.")
                continue

            thread = threading.Thread(target=self.parse_url, args=(identifier, url, config, image_container, base_url, output_folder, result_queue))
            threads.append(thread)
            thread.start()

        for thread in threads:
            thread.join(timeout=60)
            if thread.is_alive():
                self.log(self.log_widget1, f"Поток для одной из страниц завис и был пропущен")

        results = []
        while not result_queue.empty():
            result = result_queue.get()
            results.append(result)
            completed += 1
            self.show_poem(completed, total_urls)

        output_df = pd.DataFrame(results, columns=["Идентификатор", "Ссылка"] + [role for _, _, role, _ in config])
        output_path = os.path.join(output_folder, "Готовый парс.xlsx")
        try:
            output_df.to_excel(output_path, index=False)
            self.log(self.log_widget1, f"Результаты сохранены в {output_path}")
            messagebox.showinfo("Готово", f"Парсинг завершён. Результаты в {output_path}")
        except Exception as e:
            self.log(self.log_widget1, f"Ошибка сохранения файла: {e}")
            messagebox.showerror("Ошибка", f"Не удалось сохранить файл: {e}")

    # === Анализ запросов ===
    def load_file_analysis(self):
        file_path = filedialog.askopenfilename(
            title="Выберите файл с запросами",
            filetypes=(("Excel files", "*.xlsx"), ("All files", "*.*"))
        )
        if file_path:
            try:
                df = pd.read_excel(file_path)
                if "Запросы" not in df.columns:
                    self.log(self.log_widget2, "Ошибка: в файле нет колонки 'Запросы'")
                    return None
                return df
            except Exception as e:
                self.log(self.log_widget2, f"Ошибка загрузки файла: {e}")
        return None

    def select_output_file(self):
        file_path = filedialog.asksaveasfilename(
            title="Выберите папку и имя для сохранения результатов",
            defaultextension=".xlsx",
            initialfile="output.xlsx",
            filetypes=(("Excel files", "*.xlsx"), ("All files", "*.*"))
        )
        if not file_path:
            self.log(self.log_widget2, "Файл для сохранения не выбран.")
        return file_path

    def process_query(self, query, result_queue, max_retries):
        if not isinstance(query, str) or not query.strip():
            result_queue.put([query, "Пустой запрос"])
            self.log(self.log_widget2, f"Пропуск пустого запроса: {query}")
            return

        retries = 0
        while retries <= max_retries:
            self.log(self.log_widget2, f"Обрабатываю: {query} (попытка {retries + 1}/{max_retries + 1})")
            html = fetch_search_page(query)
            count = get_item_count(html) if html else "Ошибка позиций"
            if count != "0" and count != "Ошибка позиций":  # Если не ноль и не ошибка, выходим
                break
            retries += 1
            time.sleep(5)  # Пауза перед повторной попыткой

        result_queue.put([query, count])
        self.log(self.log_widget2, f"Результат: {query} — {count}")

    def start_analysis_thread(self):
        thread = threading.Thread(target=self.start_analysis)
        thread.start()

    def start_analysis(self):
        from concurrent.futures import ThreadPoolExecutor

        df = self.load_file_analysis()
        if df is None or df.empty:
            self.log(self.log_widget2, "Файл не загружен или пуст.")
            messagebox.showerror("Ошибка", "Файл не загружен или пуст.")
            return

        output_file = self.select_output_file()
        if not output_file:
            self.log(self.log_widget2, "Файл для сохранения не выбран.")
            messagebox.showerror("Ошибка", "Файл для сохранения не выбран.")
            return

        queries = df["Запросы"].tolist()
        result_queue = queue.Queue()
        max_retries = self.max_retries_var.get()
        max_workers = self.chrome_count_var.get()  # Количество одновременных Chrome

        self.log(self.log_widget2, f"Запускаю анализ: {len(queries)} запросов, {max_workers} Chrome одновременно")

        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            futures = [executor.submit(self.process_query, query, result_queue, max_retries) for query in queries]
            for future in futures:
                future.result()  # Ждём завершения всех задач

        results = []
        while not result_queue.empty():
            results.append(result_queue.get())

        output_df = pd.DataFrame(results, columns=["Запрос", "Количество"])
        output_df.to_excel(output_file, index=False)
        self.log(self.log_widget2, f"Готово! Результаты сохранены в {output_file}")
        messagebox.showinfo("Готово", f"Анализ завершён. Результаты в {output_file}")

if __name__ == "__main__":
    root = tk.Tk()
    app = App(root)
    root.mainloop()