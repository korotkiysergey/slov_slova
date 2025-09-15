import pygame
from gtts import gTTS
import os
import threading
import time


class AudioPlayer:
    def __init__(self, audio_folder=None):
        pygame.mixer.init()
        self.audio_folder = audio_folder
        if audio_folder and not os.path.exists(audio_folder):
            os.makedirs(audio_folder)

    def set_audio_folder(self, folder_path):
        """Устанавливает папку для аудиофайлов"""
        self.audio_folder = folder_path
        if not os.path.exists(folder_path):
            os.makedirs(folder_path)

    def generate_audio_file(self, word):
        """Генерирует аудиофайл для слова, если он не существует"""
        if not self.audio_folder:
            raise ValueError("Папка для аудиофайлов не установлена")

        # Создаем безопасное имя файла
        safe_filename = self._make_safe_filename(word)
        file_path = os.path.join(self.audio_folder, f"{safe_filename}.mp3")

        # Если файл уже существует, не генерируем заново
        if os.path.exists(file_path):
            return file_path

        try:
            # Генерируем аудио
            tts = gTTS(text=word, lang='ru')
            tts.save(file_path)
            return file_path
        except Exception as e:
            raise Exception(f"Ошибка генерации аудио для слова '{word}': {e}")

    def generate_all_audio_files(self, words, progress_callback=None):
        """Генерирует аудиофайлы для всех слов"""
        if not self.audio_folder:
            raise ValueError("Папка для аудиофайлов не установлена")

        generated_files = []
        total_words = len(words)

        for i, word in enumerate(words):
            try:
                file_path = self.generate_audio_file(word)
                generated_files.append(file_path)

                # Вызываем callback для обновления прогресса
                if progress_callback:
                    progress = (i + 1) / total_words * 100
                    progress_callback(progress, word)

            except Exception as e:
                print(f"Ошибка генерации файла для '{word}': {e}")
                if progress_callback:
                    progress_callback((i + 1) / total_words * 100, f"Ошибка: {word}")

        return generated_files

    def speak_word(self, word, callback=None):
        """Воспроизводит слово из сгенерированного файла"""
        thread = threading.Thread(target=self._speak_word_thread, args=(word, callback))
        thread.daemon = True
        thread.start()

    def _speak_word_thread(self, word, callback):
        """Вспомогательный метод для воспроизведения в отдельном потоке"""
        try:
            if not self.audio_folder:
                raise ValueError("Папка для аудиофайлов не установлена")

            # Формируем путь к файлу
            safe_filename = self._make_safe_filename(word)
            file_path = os.path.join(self.audio_folder, f"{safe_filename}.mp3")

            if not os.path.exists(file_path):
                # Если файл не существует, генерируем его
                file_path = self.generate_audio_file(word)

            # Воспроизводим аудио
            pygame.mixer.music.load(file_path)
            pygame.mixer.music.play()

            # Ждем завершения воспроизведения
            while pygame.mixer.music.get_busy():
                time.sleep(0.1)

        except Exception as e:
            # Передаем ошибку через callback
            if callback:
                callback(str(e))

    def _make_safe_filename(self, word):
        """Создает безопасное имя файла из слова"""
        # Заменяем небезопасные символы
        safe_chars = "абвгдежзийклмнопрстуфхцчшщъыьэюяАБВГДЕЖЗИЙКЛМНОПРСТУФХЦЧШЩЪЫЬЭЮЯabcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789-_"
        safe_filename = "".join(c if c in safe_chars else "_" for c in word)
        return safe_filename

    def cleanup(self):
        """Очистка ресурсов (теперь файлы не удаляются)"""
        # Теперь мы не удаляем файлы, они остаются для повторного использования
        pass