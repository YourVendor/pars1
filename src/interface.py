import tkinter as tk
from tkinter import filedialog, messagebox
import pandas as pd
import subprocess
from pathlib import Path
import time
import random

def load_file():
    """Загружает XLSX-файл и выводит его содержимое."""
    file_path = filedialog.askopenfilename(
        title="Выберите файл",
        filetypes=(("Excel files", "*.xlsx"), ("All files", "*.*"))
    )
    if file_path:
        try:
            # Читаем файл
            df = pd.read_excel(file_path)
            print("Загруженные данные:")
            print(df)
            return df
        except Exception as e:
            print(f"Ошибка при загрузке файла: {e}")
            return None
    return None

def start_parsing():
    """Запускает парсинг для всех ссылок из загруженного файла."""
    # Загружаем файл
    df = load_file()
    if df is None or df.empty:
        messagebox.showerror("Ошибка", "Файл не загружен или пуст.")
        return

    # Проверяем, что файл содержит нужные колонки
    if len(df.columns) < 2:
        messagebox.showerror("Ошибка", "Файл должен содержать как минимум 2 колонки: идентификатор и ссылка.")
        return

    # Создаём список для хранения результатов
    results = []

    # Проходим по каждой строке файла
    for index, row in df.iterrows():
        identifier = row[0]  # Идентификатор из первой колонки
        url = row[1]  # Ссылка из второй колонки

        if pd.isna(url) or not url.startswith("http"):
            print(f"Пропуск строки {index + 1}: некорректная ссылка.")
            continue

        print(f"Парсинг страницы: {url}")

        try:
            # Запускаем main.py с передачей URL
            main_script_path = str(Path(__file__).resolve().parent / "main.py")
            result = subprocess.run(
                ["python", main_script_path, url],
                capture_output=True,
                text=True,
                check=True
            )

            # Обрабатываем вывод main.py
            output = result.stdout.strip().split("\n")
            name = output[2].split(": ")[1] if len(output) > 0 else "N/A"
            barcode = output[3].split(": ")[1] if len(output) > 1 else "N/A"
            description = output[4].split(": ")[1] if len(output) > 2 else "N/A"

            # Добавляем результат в список
            results.append([identifier, url, name, barcode, description])

            # Случайная задержка между запросами (от 5 до 15 секунд)
            delay = random.randint(4, 9)
            print(f"Ожидание {delay} секунд перед следующим запросом...")
            time.sleep(delay)

        except subprocess.CalledProcessError as e:
            print(f"Ошибка при парсинге {url}: {e}")
            results.append([identifier, url, "Ошибка", "Ошибка", "Ошибка"])

    # Сохраняем результаты в файл
    output_df = pd.DataFrame(results, columns=["Идентификатор", "Ссылка", "Наименование", "Штрихкод", "Описание"])
    output_path = str(Path(__file__).resolve().parent.parent / "Готовый парс.xlsx")
    output_df.to_excel(output_path, index=False)
    print(f"Результаты сохранены в {output_path}")
    messagebox.showinfo("Готово", f"Парсинг завершён. Результаты сохранены в {output_path}")

def create_interface():
    """Создаёт графический интерфейс."""
    root = tk.Tk()
    root.title("Парсер")

    # Кнопка для запуска парсера
    parse_button = tk.Button(root, text="ПАРС", command=start_parsing)
    parse_button.pack(pady=10)

    root.mainloop()

if __name__ == "__main__":
    create_interface()