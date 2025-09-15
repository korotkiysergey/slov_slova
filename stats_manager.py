import json
import os
from datetime import datetime


class StatsManager:
    def __init__(self, stats_file='spelling_stats.json'):
        self.stats_file = stats_file
        self.stats = {
            'total_attempts': 0,
            'correct_attempts': 0,
            'word_stats': {},
            'session_start': datetime.now().isoformat()
        }
        self.load_stats()

    def load_stats(self):
        """Загружает статистику из файла"""
        try:
            if os.path.exists(self.stats_file):
                with open(self.stats_file, 'r', encoding='utf-8') as f:
                    self.stats = json.load(f)
        except Exception as e:
            print(f"Ошибка загрузки статистики: {e}")

    def save_stats(self):
        """Сохраняет статистику в файл"""
        try:
            with open(self.stats_file, 'w', encoding='utf-8') as f:
                json.dump(self.stats, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"Ошибка сохранения статистики: {e}")

    def reset_current_session(self):
        """Сбрасывает статистику для новой сессии"""
        self.stats['total_attempts'] = 0
        self.stats['correct_attempts'] = 0
        self.stats['word_stats'] = {}
        self.stats['session_start'] = datetime.now().isoformat()
        self.save_stats()

    def add_attempt(self, word, is_correct):
        """Добавляет попытку для слова"""
        self.stats['total_attempts'] += 1

        if is_correct:
            self.stats['correct_attempts'] += 1

        # Обновляем статистику по слову
        if word not in self.stats['word_stats']:
            self.stats['word_stats'][word] = {'attempts': 0, 'correct': 0}

        self.stats['word_stats'][word]['attempts'] += 1
        if is_correct:
            self.stats['word_stats'][word]['correct'] += 1

        self.save_stats()

    def get_current_session_errors(self):
        """Возвращает ошибки текущей сессии"""
        errors = {}
        for word, data in self.stats['word_stats'].items():
            error_count = data['attempts'] - data['correct']
            if error_count > 0:
                errors[word] = error_count
        return errors

    def get_stats(self):
        """Возвращает текущую статистику"""
        return self.stats.copy()

    def get_percentage(self):
        """Возвращает процент правильных ответов"""
        total = self.stats['total_attempts']
        correct = self.stats['correct_attempts']
        return (correct / total * 100) if total > 0 else 0

    def calculate_grade(self):
        """Вычисляет оценку по проценту правильных ответов"""
        percentage = self.get_percentage()
        if percentage >= 95:
            return 5
        elif percentage >= 85:
            return 4
        elif percentage >= 75:
            return 3
        elif percentage >= 60:
            return 2
        else:
            return 1