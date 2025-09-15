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
        self.session_results = []
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
        self.answer_entry.bind("<Return>", lambda e: self.process_and_advance())

        # Кнопки управления тренировкой
        self.buttons_frame = tk.Frame(self.training_frame)
        self.buttons_frame.pack(pady=20)

        self.speak_btn = tk.Button(self.buttons_frame, text="🔊 Прослушать слово",
                                   command=self.speak_word, font=("Arial", 12), bg="lightblue")
        self.speak_btn.pack(side="left", padx=10)

        # Динамическая кнопка для продвижения
        self.advance_btn = tk.Button(self.buttons_frame, text="➡️ Следующее слово",
                                     command=self.process_and_advance, font=("Arial", 12), bg="lightblue")
        self.advance_btn.pack(side="left", padx=10)

        # Область результата
        self.result_label = tk.Label(self.training_frame, text="", font=("Arial", 14))
        self.result_label.pack(pady=10)

        # Статистика текущей сессии
        self.stats_frame = tk.LabelFrame(self.training_frame, text="Статистика текущей сессии")
        self.stats_frame.pack(pady=10, padx=10, fill="x")

        self.stats_label = tk.Label(self.stats_frame, text="Всего попыток: 0\nПравильных ответов: 0%",
                                    font=("Arial", 10))
        self.stats_label.pack(pady=5)

    def restore_settings(self):
        """Восстанавливает предыдущие настройки"""
        if self.audio_folder:
            self.audio_player.set_audio_folder(self.audio_folder)

        # Загружаем последний использованный файл слов, если он существует
        if self.last_words_file and os.path.exists(self.last_words_file):
            try:
                self.load_words_from_file(self.last_words_file, is_start=True)
            except:
                # Если не удалось загрузить, используем стандартный список
                self.words_text.insert("1.0",
                                       "вокзал\nпарашют\nаккомпанемент\nбюллетень\nдеревня\nинтеллигент\nпрофессия\nколлектив\nтерритория\nдискуссия")
        else:
            self.words_text.insert("1.0",
                                   "вокзал\nпарашют\nаккомпанемент\nбюллетень\nдеревня\nинтеллигент\nпрофессия\nколлектив\nтерритория\nдискуссия")

    def load_words_from_file(self, filename=None, is_start=False):
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

    def prepare_and_start_training(self):
        """Подготавливает аудиофайлы и запускает тренировку"""
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
        self.session_results = []
        self.stats_manager.reset_current_session()  # Сбрасываем статистику текущей сессии

    def show_training_frame(self):
        """Показывает фрейм тренировки"""
        self.setup_frame.pack_forget()
        self.training_frame.pack(fill="both", expand=True)
        self.display_current_word()

    def display_current_word(self):
        """Отображает текущее слово для тренировки"""
        if self.current_word_index >= len(self.shuffled_words):
            self.finish_testing()
            return

        current_word = self.shuffled_words[self.current_word_index]
        self.word_info_label.config(
            text=f"Слово {self.current_word_index + 1} из {len(self.shuffled_words)} (случайный порядок)"
        )
        self.current_word_label.config(text="???")
        self.answer_entry.delete(0, tk.END)
        self.result_label.config(text="")
        self.answer_entry.focus()
        self.update_button()
        self.speak_word()

    def update_button(self):
        """Обновляет текст и стиль кнопки продвижения"""
        if self.current_word_index == len(self.shuffled_words) - 1:
            self.advance_btn.config(text="🏁 Завершить тестирование", bg="orange")
        else:
            self.advance_btn.config(text="➡️ Следующее слово", bg="lightblue")

    def speak_word(self):
        """Озвучивает текущее слово"""
        if self.current_word_index >= len(self.shuffled_words):
            return
        current_word = self.shuffled_words[self.current_word_index]
        self.audio_player.speak_word(current_word, self.on_audio_error)

    def on_audio_error(self, error_message):
        """Обработчик ошибок воспроизведения аудио"""
        self.root.after(0, lambda msg=error_message: messagebox.showerror("Ошибка",
                                                                          f"Не удалось воспроизвести слово: {msg}"))

    def process_and_advance(self, event=None):
        """Обрабатывает ввод пользователя и продвигается к следующему слову"""
        if self.current_word_index >= len(self.shuffled_words):
            return

        user_answer = self.answer_entry.get().strip()
        correct_word = self.shuffled_words[self.current_word_index]

        if not user_answer:
            messagebox.showwarning("Внимание", "Пожалуйста, введите слово!")
            return

        is_correct = user_answer.lower() == correct_word.lower()

        # Сохраняем результат сессии
        self.session_results.append((correct_word, user_answer, is_correct))

        if is_correct:
            self.result_label.config(text="Правильно! ✅", fg="green")
        else:
            self.result_label.config(text=f"Неправильно! ❌\nПравильное написание: {correct_word}", fg="red")

        # Показываем правильное написание
        self.current_word_label.config(text=correct_word)

        # Обновляем статистику
        self.stats_manager.add_attempt(correct_word, is_correct)
        self.update_stats_display()

        # Отмечаем слово как пройденное
        self.words_attempted.add(correct_word)

        # Продвигаемся дальше
        self.current_word_index += 1
        self.root.after(1000, self.display_current_word)  # Задержка для просмотра результата

    def update_stats_display(self):
        stats = self.stats_manager.get_stats()
        total = stats['total_attempts']
        correct = stats['correct_attempts']
        percentage = self.stats_manager.get_percentage()

        self.stats_label.config(
            text=f"Всего попыток: {total}\nПравильных ответов: {correct} ({percentage:.1f}%)"
        )

    def _insert_highlighted_diff(self, text_widget, user_input, correct):
        """Вставляет неправильное слово с выделением отличий"""
        i = 0
        minlen = min(len(user_input), len(correct))
        while i < minlen:
            if user_input[i] != correct[i]:
                start_pos = text_widget.index(tk.END)
                j = i
                while j < minlen and user_input[j] != correct[j]:
                    text_widget.insert(tk.END, user_input[j])
                    j += 1
                text_widget.tag_add('diff', start_pos, text_widget.index(tk.END))
                i = j
            else:
                text_widget.insert(tk.END, user_input[i])
                i += 1
        # Остаток неправильного слова
        if len(user_input) > minlen:
            start_pos = text_widget.index(tk.END)
            text_widget.insert(tk.END, user_input[minlen:])
            text_widget.tag_add('diff', start_pos, text_widget.index(tk.END))
        text_widget.insert(tk.END, " - ")
        text_widget.insert(tk.END, correct)
        text_widget.insert(tk.END, "\n")

    def finish_testing(self):
        """Завершает тестирование и показывает результаты"""
        if not self.shuffled_words:
            return

        # Получаем статистику
        grade = self.stats_manager.calculate_grade()
        stats = self.stats_manager.get_stats()
        total_words = len(self.shuffled_words)
        correct_count = stats['correct_attempts']
        errors_count = total_words - correct_count

        # Создаем окно с результатами
        results_window = tk.Toplevel(self.root)
        results_window.title("Результаты тестирования")
        results_window.geometry("700x600")
        results_window.resizable(True, True)

        # Заголовок с оценкой
        grade_label = tk.Label(results_window,
                               text=f"Оценка: {grade}",
                               font=("Arial", 20, "bold"),
                               fg="green" if grade >= 4 else "orange" if grade == 3 else "red")
        grade_label.pack(pady=10)

        # Общая статистика
        stats_text = f"Всего слов: {total_words}\n"
        stats_text += f"Правильно: {correct_count}\n"
        stats_text += f"Ошибок: {errors_count}\n"
        stats_text += f"Процент правильных ответов: {(correct_count / total_words * 100):.1f}%"

        stats_label = tk.Label(results_window, text=stats_text, font=("Arial", 14))
        stats_label.pack(pady=10)

        # Неправильные слова
        incorrect_frame = tk.LabelFrame(results_window, text="Неправильно написанные слова")
        incorrect_frame.pack(pady=10, padx=10, fill="both", expand=True)

        inc_text = scrolledtext.ScrolledText(incorrect_frame, font=("Arial", 11), wrap=tk.WORD, height=8)
        inc_text.pack(pady=5, padx=5, fill="both", expand=True)
        inc_text.tag_config('diff', foreground='red')

        if errors_count == 0:
            inc_text.insert(tk.END, "Все слова написаны правильно! 🎉")
        else:
            for correct, user, is_c in self.session_results:
                if not is_c:
                    self._insert_highlighted_diff(inc_text, user, correct)
        inc_text.config(state="disabled")

        # Правильные слова
        correct_frame = tk.LabelFrame(results_window, text="Правильно написанные слова")
        correct_frame.pack(pady=10, padx=10, fill="both", expand=True)

        cor_text = scrolledtext.ScrolledText(correct_frame, font=("Arial", 11), wrap=tk.WORD, height=8)
        cor_text.pack(pady=5, padx=5, fill="both", expand=True)

        if correct_count == 0:
            cor_text.insert(tk.END, "Нет правильно написанных слов.")
        else:
            for correct, _, is_c in self.session_results:
                if is_c:
                    cor_text.insert(tk.END, f"• {correct}\n")
        cor_text.config(state="disabled")

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
        results_window.update_idletasks()
        x = (results_window.winfo_screenwidth() - results_window.winfo_width()) // 2
        y = (results_window.winfo_screenheight() - results_window.winfo_height()) // 2
        results_window.geometry(f"+{x}+{y}")

    def _retry_testing(self, results_window):
        """Перезапускает тестирование"""
        results_window.destroy()
        self.shuffle_words()
        self.display_current_word()

    def show_setup_frame(self):
        """Показывает фрейм настройки"""
        self.training_frame.pack_forget()
        self.setup_frame.pack(fill="both", expand=True)

    def cleanup(self):
        """Очистка ресурсов"""
        self.audio_player.cleanup()