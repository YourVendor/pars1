import tkinter as tk
from tkinter import filedialog
import pandas as pd
import subprocess
from pathlib import Path  # Для работы с путями

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
        except Exception as e:
            print(f"Ошибка при загрузке файла: {e}")

def start_parsing():
    """Запускает скрипт main.py для парсинга."""
    try:
        # Получаем абсолютный путь к main.py
        main_script_path = str(Path(__file__).resolve().parent / "main.py")
        
        # Запускаем main.py через subprocess
        subprocess.run(["python", main_script_path], check=True)
        print("Парсинг завершён!")
    except subprocess.CalledProcessError as e:
        print(f"Ошибка при запуске парсера: {e}")
    except FileNotFoundError:
        print("Ошибка: файл main.py не найден.")

def create_interface():
    """Создаёт графический интерфейс."""
    root = tk.Tk()
    root.title("Парсер")

    # Кнопка для загрузки файла
    load_button = tk.Button(root, text="Загрузить файл", command=load_file)
    load_button.pack(pady=10)

    # Кнопка для запуска парсера
    parse_button = tk.Button(root, text="ПАРС", command=start_parsing)
    parse_button.pack(pady=10)

    root.mainloop()

if __name__ == "__main__":
    create_interface()