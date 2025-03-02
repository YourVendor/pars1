# app.py
import sys
import os
import traceback
from src.interface import create_interface

def resource_path(relative_path):
    """Возвращает путь к ресурсу в сборке или исходной папке"""
    if hasattr(sys, '_MEIPASS'):
        return os.path.join(sys._MEIPASS, relative_path)
    return os.path.join(os.path.dirname(__file__), relative_path)

if __name__ == "__main__":
    print("Запуск приложения...")
    print(f"poems.txt существует: {os.path.exists(resource_path('poems.txt'))}")
    print(f"parser.ico существует: {os.path.exists(resource_path('parser.ico'))}")
    try:
        create_interface()
    except Exception as e:
        print(f"Ошибка: {e}")
        traceback.print_exc()
        input("Нажмите Enter для выхода...")