"""Persistence checks isolated from the user's settings and API credentials."""
import tempfile
import unittest
from pathlib import Path
from avaturn_live_streamer.local_settings import SettingsStore

class Persistence(unittest.TestCase):
    def test_reopen_and_merge_preserves_provider_settings(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / 'settings.sqlite3'
            SettingsStore(path).update({'provider_deepseek_model':'deepseek-chat','text_provider':'deepseek'})
            SettingsStore(path).update({'text_provider':'openai'})
            self.assertEqual(SettingsStore(path).read(), {'provider_deepseek_model':'deepseek-chat','text_provider':'openai'})

    def test_invalid_batch_does_not_write_partial_settings(self):
        with tempfile.TemporaryDirectory() as folder:
            store = SettingsStore(Path(folder) / 'settings.sqlite3')
            store.update({'keep':'value'})
            with self.assertRaises(ValueError):
                store.update({'keep':'changed','bad':[]})
            self.assertEqual(store.read(), {'keep':'value'})
            store.update({'keep':None})
            self.assertEqual(store.read(), {})

if __name__ == '__main__':
    unittest.main()
