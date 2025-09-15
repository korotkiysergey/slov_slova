import tkinter as tk
from audio_player import AudioPlayer
from stats_manager import StatsManager
from gui import SpellingTrainerGUI
import json
import os


def main():
    root = tk.Tk()

    # Загрузка настроек
    settings = load_settings()

    # Инициализация компонентов
    audio_player = AudioPlayer(settings.get('audio_folder'))
    stats_manager = StatsManager()
    app = SpellingTrainerGUI(root, audio_player, stats_manager, settings)

    # Обработка закрытия окна
    def on_closing():
        app.cleanup()
        root.destroy()

    root.protocol("WM_DELETE_WINDOW", on_closing)
    root.mainloop()


def load_settings():
    """Загружает настройки из файла"""
    settings_file = 'spelling_trainer_settings.json'
    default_settings = {
        'audio_folder': '',
        'last_words_file': ''
    }

    try:
        if os.path.exists(settings_file):
            with open(settings_file, 'r', encoding='utf-8') as f:
                return json.load(f)
    except Exception as e:
        print(f"Ошибка загрузки настроек: {e}")

    return default_settings


def save_settings(settings):
    """Сохраняет настройки в файл"""
    try:
        with open('spelling_trainer_settings.json', 'w', encoding='utf-8') as f:
            json.dump(settings, f, ensure_ascii=False, indent=2)
    except Exception as e:
        print(f"Ошибка сохранения настроек: {e}")


if __name__ == "__main__":
    main()