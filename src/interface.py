import tkinter as tk
from tkinter import filedialog
import pandas as pd

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

def create_interface():
    """Создаёт графический интерфейс."""
    root = tk.Tk()
    root.title("Парсер")

    # Кнопка для загрузки файла
    load_button = tk.Button(root, text="Загрузить файл", command=load_file)
    load_button.pack(pady=20)

    root.mainloop()

if __name__ == "__main__":
    create_interface()