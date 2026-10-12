import datetime as dt
import importlib.util
from pathlib import Path
import re
import sqlite3
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('bootlog', ROOT / 'bootlog.py')
bootlog = importlib.util.module_from_spec(spec)
spec.loader.exec_module(bootlog)


class BootDisplayTests(unittest.TestCase):
    def setUp(self):
        self.now = dt.datetime.now().astimezone().replace(hour=12, minute=0, second=0)

    def row(self, identity, hour, minute=0, source='kernel boot time', days=0):
        date = self.now.replace(hour=hour, minute=minute) - dt.timedelta(days=days)
        return identity, date.timestamp(), source

    def test_first_boot_remains_after_reboot(self):
        result = bootlog.display([self.row('later', 10, 15), self.row('first', 7, 1)], self.now)
        self.assertEqual(result['label'], 'First boot 7:01 am')
        self.assertEqual(result['today_count'], 2)
        self.assertIn('First: 7:01 am\nReboot: 10:15 am', result['tooltip'])

    def test_overnight_is_not_a_new_boot(self):
        result = bootlog.display([self.row('yesterday', 8, days=1)], self.now)
        self.assertEqual(result['label'], 'No boot today')
        self.assertEqual(result['today_count'], 0)

    def test_empty_history(self):
        self.assertEqual(bootlog.display([], self.now)['label'], 'No boot today')

    def test_approximate_first_boot_is_labelled(self):
        result = bootlog.display([self.row('old', 7, 1, 'journal first entry (approximate)')], self.now)
        self.assertEqual(result['label'], 'First boot ~7:01 am')
        self.assertIn('(approx.)', result['tooltip'])

    def test_prior_days_do_not_change_today(self):
        result = bootlog.display([self.row('old', 3, days=1), self.row('new', 9)], self.now)
        self.assertEqual(result['label'], 'First boot 9:00 am')

    def test_stale_recorder_reports_attention(self):
        with sqlite3.connect(':memory:') as db:
            db.execute('CREATE TABLE boots (id TEXT, epoch REAL, source TEXT)')
            db.execute('CREATE TABLE meta (key TEXT, value TEXT)')
            with patch.object(bootlog, 'current_boot', return_value=('test', 0)):
                self.assertEqual(bootlog.status(db)['label'], 'Boot log needs attention')


class ThemeContractTests(unittest.TestCase):
    def test_native_bar_theme_inheritance(self):
        qml = (ROOT / 'BarWidget.qml').read_text()
        self.assertIn('WidgetButton {', qml)
        self.assertIn('bar: root.bar', qml)
        self.assertIn('fontSize: Style.font.body * 1.15', qml)
        self.assertIsNone(re.search(r'^\s*(foreground|fontFamily|color)\s*:', qml, re.M))
        self.assertIsNone(re.search(r'#[0-9a-fA-F]{6}', qml))

    def test_history_uses_terminal_without_theme_override(self):
        qml = (ROOT / 'BarWidget.qml').read_text()
        self.assertIn('["ghostty", "-e", "python3", root.helper, "history"]', qml)


if __name__ == '__main__':
    unittest.main()
