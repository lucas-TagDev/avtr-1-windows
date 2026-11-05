"""Small project-local SQLite settings store. Values may contain API keys."""
from contextlib import closing
import sqlite3
from pathlib import Path

DATABASE = Path(__file__).resolve().parents[2] / 'settings.sqlite3'


class SettingsStore:
    def __init__(self, path=DATABASE):
        self.path = Path(path)

    def connect(self):
        connection = sqlite3.connect(self.path, timeout=10)
        connection.execute('CREATE TABLE IF NOT EXISTS settings (key TEXT PRIMARY KEY, value TEXT NOT NULL)')
        return connection

    def read(self):
        with closing(self.connect()) as connection:
            return dict(connection.execute('SELECT key, value FROM settings'))

    def update(self, values):
        if not isinstance(values, dict) or len(values) > 200:
            raise ValueError('Configurações inválidas')
        for key, value in values.items():
            if not isinstance(key, str) or len(key) > 120 or not key:
                raise ValueError('Nome de configuração inválido')
            if value is not None and (not isinstance(value, str) or len(value) > 50000):
                raise ValueError('Valor de configuração inválido')
        with closing(self.connect()) as connection, connection:
            for key, value in values.items():
                if value is None:
                    connection.execute('DELETE FROM settings WHERE key=?', (key,))
                else:
                    connection.execute('INSERT INTO settings VALUES (?, ?) ON CONFLICT(key) DO UPDATE SET value=excluded.value', (key, value))
