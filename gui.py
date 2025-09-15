import tkinter as tk
from tkinter import scrolledtext, messagebox, Frame, filedialog, ttk
import random
import threading
import os
import json


class SpellingTrainerGUI:
    def __init__(self, root, audio_player, stats_manager, settings):
        self.root = root
        self.audio_player = audio_player
        self.stats_manager = stats_manager
        self.settings = settings

        self.words_attempted = set()
        self.words = []
        self.shuffled_words = []
        self.current_word_index = 0
        self.audio_folder = settings.get('audio_folder', '')
        self.last_words_file = settings.get('last_words_file', '')

        self.root.title("Тренажер правописания русских слов")
        self.root.geometry("900x650")

        # Создаем основные фреймы
        self.setup_frame = Frame(self.root)
        self.training_frame = Frame(self.root)

        self.create_setup_widgets()
        self.create_training_widgets()

        # Восстанавливаем предыдущие настройки
        self.restore_settings()

        # Показываем только фрейм настройки
        self.show_setup_frame()

    def create_setup_widgets(self):
        """Создает виджеты для настройки списка слов"""
        # Область для выбора папки
        self.folder_frame = tk.LabelFrame(self.setup_frame, text="Папка для аудиофайлов")
        self.folder_frame.pack(pady=10, padx=10, fill="x")

        self.folder_path_var = tk.StringVar(value=self.audio_folder)
        self.folder_entry = tk.Entry(self.folder_frame, textvariable=self.folder_path_var,
                                     font=("Arial", 10), state="readonly")
        self.folder_entry.pack(side="left", fill="x", expand=True, padx=5, pady=5)

        self.browse_btn = tk.Button(self.folder_frame, text="Выбрать папку",
                                    command=self.browse_folder, font=("Arial", 10))
        self.browse_btn.pack(side="right", padx=5, pady=5)

        # Область для загрузки/сохранения списка слов
        self.file_buttons_frame = tk.Frame(self.setup_frame)
        self.file_buttons_frame.pack(pady=5, padx=10, fill="x")

        self.load_words_btn = tk.Button(self.file_buttons_frame, text="📂 Загрузить слова из файла",
                                        command=self.load_words_from_file, font=("Arial", 10))
        self.load_words_btn.pack(side="left", padx=5)

        self.save_words_btn = tk.Button(self.file_buttons_frame, text="💾 Сохранить слова в файл",
                                        command=self.save_words_to_file, font=("Arial", 10))
        self.save_words_btn.pack(side="left", padx=5)

        # Область для ввода списка слов
        self.words_frame = tk.LabelFrame(self.setup_frame, text="Список слов для изучения")
        self.words_frame.pack(pady=10, padx=10, fill="both", expand=True)

        instruction_label = tk.Label(self.words_frame,
                                     text="Введите слова для изучения (по одному на строку):",
                                     font=("Arial", 10))
        instruction_label.pack(pady=5)

        self.words_text = scrolledtext.ScrolledText(self.words_frame, height=12, font=("Arial", 12))
        self.words_text.pack(pady=10, padx=10, fill="both", expand=True)

        # Прогресс-бар для генерации файлов
        self.progress_frame = tk.Frame(self.setup_frame)
        self.progress_frame.pack(pady=5, padx=10, fill="x")

        self.progress_label = tk.Label(self.progress_frame, text="", font=("Arial", 9))
        self.progress_label.pack()

        self.progress_bar = ttk.Progressbar(self.progress_frame, mode='determinate')
        self.progress_bar.pack(fill="x", pady=5)
        self.progress_bar.pack_forget()  # Скрываем изначально

        # Кнопка начала тренировки
        self.start_btn = tk.Button(self.setup_frame, text="Подготовить аудиофайлы и начать тренировку",
                                   command=self.prepare_and_start_training, font=("Arial", 12), bg="lightgreen")
        self.start_btn.pack(pady=10)

    def create_training_widgets(self):
        """Создает виджеты для режима тренировки"""
        # Кнопка возврата к настройкам
        self.back_btn = tk.Button(self.training_frame, text="← Назад к настройкам",
                                  command=self.show_setup_frame, font=("Arial", 10))
        self.back_btn.pack(anchor="nw", pady=5, padx=5)

        # Область текущего слова
        self.word_info_label = tk.Label(self.training_frame, text="", font=("Arial", 10))
        self.word_info_label.pack(pady=5)

        self.current_word_label = tk.Label(self.training_frame, text="Нажмите 'Следующее слово' чтобы начать",
                                           font=("Arial", 16, "bold"))
        self.current_word_label.pack(pady=20)

        # Поле для ввода ответа
        self.answer_frame = tk.Frame(self.training_frame)
        self.answer_frame.pack(pady=20)

        tk.Label(self.answer_frame, text="Напишите услышанное слово:", font=("Arial", 12)).pack()
        self.answer_entry = tk.Entry(self.answer_frame, font=("Arial", 16), width=30)
        self.answer_entry.pack(pady=10)
        self.answer_entry.bind("<Return>", self.check_answer)

        # Кнопки управления тренировкой
        self.buttons_frame = tk.Frame(self.training_frame)
        self.buttons_frame.pack(pady=20)

        self.speak_btn = tk.Button(self.buttons_frame, text="🔊 Прослушать слово",
                                   command=self.speak_word, font=("Arial", 12), bg="lightblue")
        self.speak_btn.pack(side="left", padx=10)

        self.check_btn = tk.Button(self.buttons_frame, text="✓ Проверить",
                                   command=self.check_answer, font=("Arial", 12), bg="lightgreen")
        self.check_btn.pack(side="left", padx=10)

        # Добавим кнопку завершения тестирования
        self.finish_btn = tk.Button(self.buttons_frame, text="🏁 Завершить тестирование",
                                   command=self.finish_testing, font=("Arial", 12), bg="orange")
        self.finish_btn.pack(side="left", padx=10)

        # Область результата
        self.result_label = tk.Label(self.training_frame, text="", font=("Arial", 14))
        self.result_label.pack(pady=10)

        # Статистика текущей сессии
        self.stats_frame = tk.LabelFrame(self.training_frame, text="Статистика текущей сессии")
        self.stats_frame.pack(pady=10, padx=10, fill="x")

        self.stats_label = tk.Label(self.stats_frame, text="Всего попыток: 0\nПравильных ответов: 0%",
                                    font=("Arial", 10))
        self.stats_label.pack(pady=5)

        # Кнопка показа полной статистики
        self.show_stats_btn = tk.Button(self.stats_frame, text="📊 Показать полную статистику",
                                        command=self.show_full_stats, font=("Arial", 10))
        self.show_stats_btn.pack(pady=5)

    def restore_settings(self):
        """Восстанавливает предыдущие настройки"""
        if self.audio_folder:
            self.audio_player.set_audio_folder(self.audio_folder)

        # Загружаем последний использованный файл слов, если он существует
        if self.last_words_file and os.path.exists(self.last_words_file):
            try:
                self.load_words_from_file(self.last_words_file, is_start = True)
            except:
                # Если не удалось загрузить, используем стандартный список
                self.words_text.insert("1.0",
                                       "вокзал\nпарашют\nаккомпанемент\nбюллетень\nдеревня\nинтеллигент\nпрофессия\nколлектив\nтерритория\nдискуссия")
        else:
            self.words_text.insert("1.0",
                                   "вокзал\nпарашют\nаккомпанемент\nбюллетень\nдеревня\nинтеллигент\nпрофессия\nколлектив\nтерритория\nдискуссия")

    def load_words_from_file(self, filename=None, is_start = False):
        """Загружает слова из текстового файла"""
        if not filename:
            filename = filedialog.askopenfilename(
                title="Выберите файл со словами",
                filetypes=[("Текстовые файлы", "*.txt"), ("Все файлы", "*.*")]
            )
            if not filename:
                return

        try:
            with open(filename, 'r', encoding='utf-8') as f:
                words_content = f.read().strip()

            # Очищаем текстовое поле и вставляем новые слова
            self.words_text.delete("1.0", tk.END)
            self.words_text.insert("1.0", words_content)

            # Сохраняем путь к файлу в настройках
            self.last_words_file = filename
            self.save_settings()

            if not is_start:
                messagebox.showinfo("Успех", f"Слова загружены из файла: {os.path.basename(filename)}")

        except Exception as e:
            messagebox.showerror("Ошибка", f"Не удалось загрузить файл:\n{str(e)}")

    def save_words_to_file(self):
        """Сохраняет слова в текстовый файл"""
        filename = filedialog.asksaveasfilename(
            title="Сохранить слова в файл",
            defaultextension=".txt",
            filetypes=[("Текстовые файлы", "*.txt"), ("Все файлы", "*.*")]
        )
        if not filename:
            return

        try:
            words_content = self.words_text.get("1.0", tk.END).strip()
            with open(filename, 'w', encoding='utf-8') as f:
                f.write(words_content)

            # Сохраняем путь к файлу в настройках
            self.last_words_file = filename
            self.save_settings()

            messagebox.showinfo("Успех", f"Слова сохранены в файл: {os.path.basename(filename)}")

        except Exception as e:
            messagebox.showerror("Ошибка", f"Не удалось сохранить файл:\n{str(e)}")

    def save_settings(self):
        """Сохраняет текущие настройки"""
        self.settings['audio_folder'] = self.audio_folder
        self.settings['last_words_file'] = self.last_words_file

        # Сохраняем в файл (функция будет добавлена в main.py)
        try:
            from main import save_settings
            save_settings(self.settings)
        except:
            pass

    def browse_folder(self):
        """Открывает диалог выбора папки"""
        folder = filedialog.askdirectory(
            title="Выберите папку для сохранения аудиофайлов",
            initialdir=self.audio_folder if self.audio_folder else None
        )
        if folder:
            self.folder_path_var.set(folder)
            self.audio_folder = folder
            self.audio_player.set_audio_folder(folder)
            self.save_settings()

    def show_setup_frame(self):
        """Показывает фрейм настройки и скрывает фрейм тренировки"""
        self.training_frame.pack_forget()
        self.setup_frame.pack(fill="both", expand=True)

    def show_training_frame(self):
        """Показывает фрейм тренировки и скрывает фрейм настройки"""
        self.setup_frame.pack_forget()
        self.training_frame.pack(fill="both", expand=True)
        self.answer_entry.focus()

    def prepare_and_start_training(self):
        """Подготавливает аудиофайлы и начинает тренировку"""
        if not self.audio_folder:
            messagebox.showwarning("Внимание", "Пожалуйста, выберите папку для сохранения аудиофайлов!")
            return

        text = self.words_text.get("1.0", tk.END).strip()
        self.words = [word.strip() for word in text.split('\n') if word.strip()]

        if not self.words:
            messagebox.showwarning("Внимание", "Пожалуйста, введите хотя бы одно слово!")
            return

        if len(self.words) < 2:
            messagebox.showwarning("Внимание", "Добавьте хотя бы 2 слова для эффективной тренировки!")
            return

        # Отключаем кнопку на время генерации
        self.start_btn.config(state="disabled", text="Генерация аудиофайлов...")
        self.progress_bar.pack(fill="x", pady=5)
        self.progress_label.config(text="Подготовка аудиофайлов...")

        # Запускаем генерацию в отдельном потоке
        threading.Thread(target=self._generate_audio_files, daemon=True).start()

    def _generate_audio_files(self):
        """Генерирует аудиофайлы в отдельном потоке"""
        try:
            def progress_callback(progress, current_word):
                # Обновляем UI в основном потоке
                self.root.after(0, lambda: self._update_progress(progress, current_word))

            # Генерируем файлы
            self.audio_player.generate_all_audio_files(self.words, progress_callback)

            # Завершаем и запускаем тренировку
            self.root.after(0, self._finish_preparation)

        except Exception as e:
            self.root.after(0, lambda: self._handle_generation_error(str(e)))

    def _update_progress(self, progress, current_word):
        """Обновляет прогресс-бар"""
        self.progress_bar["value"] = progress
        if "Ошибка:" in str(current_word):
            self.progress_label.config(text=f"Прогресс: {progress:.0f}% - {current_word}")
        else:
            self.progress_label.config(text=f"Прогресс: {progress:.0f}% - Генерация: {current_word}")

    def _finish_preparation(self):
        """Завершает подготовку и запускает тренировку"""
        self.progress_bar.pack_forget()
        self.progress_label.config(text="")
        self.start_btn.config(state="normal", text="Подготовить аудиофайлы и начать тренировку")

        # Сохраняем настройки
        self.save_settings()

        # Перемешиваем слова и начинаем тренировку
        self.shuffle_words()
        self.show_training_frame()
        self.next_word()

    def _handle_generation_error(self, error_message):
        """Обрабатывает ошибки генерации"""
        self.progress_bar.pack_forget()
        self.progress_label.config(text="")
        self.start_btn.config(state="normal", text="Подготовить аудиофайлы и начать тренировку")
        messagebox.showerror("Ошибка", f"Ошибка при генерации аудиофайлов:\n{error_message}")

    def shuffle_words(self):
        """Перемешивает порядок слов"""
        self.shuffled_words = self.words.copy()
        random.shuffle(self.shuffled_words)
        self.current_word_index = 0
        self.words_attempted.clear()  # Сбрасываем отслеживание пройденных слов
        self.stats_manager.reset_current_session()  # Сбрасываем статистику текущей сессии

    def speak_word(self):
        """Озвучивает текущее слово"""
        if not self.shuffled_words:
            return

        current_word = self.shuffled_words[self.current_word_index]
        self.audio_player.speak_word(current_word, self.on_audio_error)

    def on_audio_error(self, error_message):
        """Обработчик ошибок воспроизведения аудио"""
        self.root.after(0, lambda msg=error_message: messagebox.showerror("Ошибка",
                                                                          f"Не удалось воспроизвести слово: {msg}"))

    def next_word(self):
        if not self.shuffled_words:
            return

        self.current_word_index = (self.current_word_index + 1) % len(self.shuffled_words)
        self.answer_entry.delete(0, tk.END)
        self.result_label.config(text="")

        # Обновляем информацию о текущем слове
        self.word_info_label.config(
            text=f"Слово {self.current_word_index} из {len(self.shuffled_words)} (порядок случайный)"
        )
        self.current_word_label.config(text="???")

        self.answer_entry.focus()
        self.speak_word()

    def check_answer(self, event=None):
        if not self.shuffled_words:
            return

        user_answer = self.answer_entry.get().strip()
        correct_word = self.shuffled_words[self.current_word_index]

        if not user_answer:
            messagebox.showwarning("Внимание", "Пожалуйста, введите слово!")
            return

        is_correct = user_answer.lower() == correct_word.lower()

        if is_correct:
            self.result_label.config(text="Правильно! ✅", fg="green")
        else:
            self.result_label.config(text=f"Неправильно! ❌\nПравильный ответ: {correct_word}", fg="red")

        # Показываем правильное написание
        self.current_word_label.config(text=correct_word)

        # Обновляем статистику
        self.stats_manager.add_attempt(correct_word, is_correct, user_answer.lower())
        self.update_stats_display()

        # Отмечаем слово как пройденное
        self.words_attempted.add(correct_word)

        # Проверяем, все ли слова пройдены
        if len(self.words_attempted) >= len(self.shuffled_words):
            self.root.after(1000, self.finish_testing)  # Завершаем через секунду
        else:
            # Показываем следующее слово
            self.root.after(1000, self.next_word)  # Задержка 1 секунда перед следующим словом

    def update_stats_display(self):
        stats = self.stats_manager.get_stats()
        total = stats['total_attempts']
        correct = stats['correct_attempts']
        percentage = self.stats_manager.get_percentage()

        self.stats_label.config(
            text=f"Всего попыток: {total}\nПравильных ответов: {correct} ({percentage:.1f}%)"
        )

    def show_full_stats(self):
        stats_window = tk.Toplevel(self.root)
        stats_window.title("Полная статистика")
        stats_window.geometry("500x400")

        text_area = scrolledtext.ScrolledText(stats_window, font=("Arial", 10))
        text_area.pack(pady=10, padx=10, fill="both", expand=True)

        stats = self.stats_manager.get_stats()
        stats_text = "СТАТИСТИКА ПО СЛОВАМ:\n\n"

        for word, data in stats['word_stats'].items():
            attempts = data['attempts']
            correct = data['correct']
            percentage = (correct / attempts * 100) if attempts > 0 else 0
            stats_text += f"{word}: {correct}/{attempts} ({percentage:.1f}%)\n"

        stats_text += f"\nОбщая статистика:\n"
        stats_text += f"Всего попыток: {stats['total_attempts']}\n"
        stats_text += f"Правильных ответов: {stats['correct_attempts']}\n"
        stats_text += f"Сессия начата: {stats['session_start']}\n"
        stats_text += f"Папка аудиофайлов: {self.audio_folder}"

        text_area.insert("1.0", stats_text)
        text_area.config(state="disabled")

    def cleanup(self):
        """Очистка ресурсов"""
        self.audio_player.cleanup()

    def _retry_testing(self, results_window):
        """Перезапускает тестирование"""
        results_window.destroy()
        self.shuffle_words()
        self.next_word()

    def finish_testing(self):
        """Завершает тестирование и показывает результаты"""
        if not self.shuffled_words:
            return

        # Получаем статистику ошибок
        errors = self.stats_manager.get_current_session_errors()
        grade = self.stats_manager.calculate_grade()

        # Создаем окно с результатами
        results_window = tk.Toplevel(self.root)
        results_window.title("Результаты тестирования")
        results_window.geometry("600x500")
        results_window.resizable(True, True)

        # Заголовок с оценкой
        grade_label = tk.Label(results_window,
                               text=f"Оценка: {grade}",
                               font=("Arial", 20, "bold"),
                               fg="green" if grade >= 4 else "orange" if grade == 3 else "red")
        grade_label.pack(pady=10)

        # Статистика
        total_words = len(self.shuffled_words)
        correct_words = total_words - sum(errors.values())
        errors_count = sum(errors.values())

        stats_text = f"Всего слов: {total_words}\n"
        stats_text += f"Правильно: {correct_words}\n"
        stats_text += f"Ошибок: {errors_count}\n"
        stats_text += f"Процент правильных ответов: {(correct_words / total_words * 100):.1f}%"

        stats_label = tk.Label(results_window, text=stats_text, font=("Arial", 14))
        stats_label.pack(pady=10)

        # Детализация ошибок
        if errors:
            errors_frame = tk.LabelFrame(results_window, text="Ошибочные слова", font=("Arial", 12))
            errors_frame.pack(pady=10, padx=10, fill="both", expand=True)

            errors_text = scrolledtext.ScrolledText(errors_frame, font=("Arial", 11))
            errors_text.pack(pady=5, padx=5, fill="both", expand=True)

            errors_content = "Слова с ошибками:\n\n"
            for word, error_count in errors.items():
                errors_content += f"• {word}: {error_count} ошибок\n"

            errors_text.insert("1.0", errors_content)
            errors_text.config(state="disabled")
        else:
            no_errors_label = tk.Label(results_window, text="Все слова написаны правильно! 🎉",
                                       font=("Arial", 14), fg="green")
            no_errors_label.pack(pady=20)

        # Кнопки
        buttons_frame = tk.Frame(results_window)
        buttons_frame.pack(pady=10)

        retry_btn = tk.Button(buttons_frame, text="🔄 Повторить тестирование",
                              command=lambda: self._retry_testing(results_window),
                              font=("Arial", 12), bg="lightblue")
        retry_btn.pack(side="left", padx=5)

        close_btn = tk.Button(buttons_frame, text="✓ Завершить",
                              command=results_window.destroy,
                              font=("Arial", 12), bg="lightgreen")
        close_btn.pack(side="left", padx=5)

        # Центрируем окно
        results_window.transient(self.root)
        results_window.grab_set()
        results_window.focus_set()

        # Центрируем окно на экране
        results_window.update_idletasks()
        x = (results_window.winfo_screenwidth() - results_window.winfo_width()) // 2
        y = (results_window.winfo_screenheight() - results_window.winfo_height()) // 2
        results_window.geometry(f"+{x}+{y}")
