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

    def get_stats(self):
        """Возвращает текущую статистику"""
        return self.stats.copy()

    def get_percentage(self):
        """Возвращает процент правильных ответов"""
        total = self.stats['total_attempts']
        correct = self.stats['correct_attempts']
        return (correct / total * 100) if total > 0 else 0