#!/usr/bin/env python3
"""Unit tests for SRCC testable logic functions."""

import sys
import os
import json
import tempfile
import unittest
from datetime import datetime, timedelta
from unittest.mock import patch, MagicMock

# Add srcc to path
sys.path.insert(0, '/home/juanpaez/.nanobot/workspace/dev/srcc')

# Test data - matches actual data.json structure
test_data = {
    "chores": [
        {"id": 1, "name": "Test chore daily", "schedule": "daily", "last_done": None},
        {"id": 2, "name": "Test chore weekly", "schedule": "weekly", "last_done": None},
        {"id": 3, "name": "Test chore done yesterday", "schedule": "daily", "last_done": "2026-02-23"}
    ],
    "checkins": {},
    "daily_forms": {}
}


class TestLoadSaveData(unittest.TestCase):
    """Test data persistence functions."""

    def setUp(self):
        # Create NEW temp data file for each test
        self.temp_file = tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False)
        json.dump(test_data, self.temp_file)
        self.temp_file.close()
        
        # Patch DATA_FILE in app module
        import app as app_module
        self.original_data_file = app_module.DATA_FILE
        app_module.DATA_FILE = self.temp_file.name

    def tearDown(self):
        # Restore original
        import app as app_module
        app_module.DATA_FILE = self.original_data_file
        os.unlink(self.temp_file.name)

    def test_load_data_returns_dict(self):
        """load_data should return a dictionary."""
        import app
        data = app.load_data()
        self.assertIsInstance(data, dict)

    def test_load_data_has_chores(self):
        """load_data should contain chores key."""
        import app
        data = app.load_data()
        self.assertIn('chores', data)

    def test_load_data_has_checkins(self):
        """load_data should contain checkins key."""
        import app
        data = app.load_data()
        self.assertIn('checkins', data)


class TestGetTodayChores(unittest.TestCase):
    """Test get_today_chores logic."""

    def setUp(self):
        # Create NEW temp data file for each test
        self.temp_file = tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False)
        json.dump(test_data, self.temp_file)
        self.temp_file.close()
        
        import app as app_module
        self.original_data_file = app_module.DATA_FILE
        app_module.DATA_FILE = self.temp_file.name

    def tearDown(self):
        import app as app_module
        app_module.DATA_FILE = self.original_data_file
        os.unlink(self.temp_file.name)

    def test_returns_list(self):
        """Should return a list."""
        import app
        result = app.get_today_chores()
        self.assertIsInstance(result, list)

    def test_includes_daily_chores(self):
        """Daily chores should appear in today's list."""
        import app
        result = app.get_today_chores()
        # Should have at least the daily chores
        self.assertGreaterEqual(len(result), 2)


class TestGetOverdueChores(unittest.TestCase):
    """Test get_overdue_chores logic."""

    def setUp(self):
        self.temp_file = tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False)
        json.dump(test_data, self.temp_file)
        self.temp_file.close()
        
        import app as app_module
        self.original_data_file = app_module.DATA_FILE
        app_module.DATA_FILE = self.temp_file.name

    def tearDown(self):
        import app as app_module
        app_module.DATA_FILE = self.original_data_file
        os.unlink(self.temp_file.name)

    def test_returns_list(self):
        """Should return a list."""
        import app
        result = app.get_overdue_chores()
        self.assertIsInstance(result, list)


class TestDateLogic(unittest.TestCase):
    """Test date comparison logic used in chore filtering."""

    def test_is_today(self):
        """Date from today should be detected."""
        today = datetime.now().strftime('%Y-%m-%d')
        self.assertEqual(today, '2026-02-24')

    def test_is_yesterday(self):
        """Date from yesterday should be detected."""
        yesterday = (datetime.now() - timedelta(days=1)).strftime('%Y-%m-%d')
        self.assertEqual(yesterday, '2026-02-23')

    def test_parse_chore_last_done(self):
        """Chore last_done date should parse correctly."""
        test_date = "2026-02-23"
        parsed = datetime.strptime(test_date, '%Y-%m-%d')
        self.assertEqual(parsed.year, 2026)
        self.assertEqual(parsed.month, 2)
        self.assertEqual(parsed.day, 23)

    def test_days_between_dates(self):
        """Days between two dates should calculate correctly."""
        date1 = datetime(2026, 2, 23)
        date2 = datetime(2026, 2, 24)
        self.assertEqual((date2 - date1).days, 1)


class TestWeatherParsing(unittest.TestCase):
    """Test weather data parsing (mocked)."""

    def setUp(self):
        self.temp_file = tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False)
        json.dump(test_data, self.temp_file)
        self.temp_file.close()
        
        import app as app_module
        self.original_data_file = app_module.DATA_FILE
        app_module.DATA_FILE = self.temp_file.name

    def tearDown(self):
        import app as app_module
        app_module.DATA_FILE = self.original_data_file
        os.unlink(self.temp_file.name)

    @patch('app.requests.get')
    def test_weather_returns_dict(self, mock_get):
        """get_weather should return a dict."""
        mock_response = MagicMock()
        mock_response.json.return_value = {
            'current': {'temp_c': 15, 'condition': {'text': 'Sunny'}},
            'location': {'name': 'Kirkland'}
        }
        mock_response.raise_for_status = MagicMock()
        mock_get.return_value = mock_response
        
        import app
        result = app.get_weather()
        self.assertIsInstance(result, dict)


class TestConfigImports(unittest.TestCase):
    """Test that config loads correctly."""

    def test_config_imports(self):
        """config module should import."""
        import config
        self.assertIsNotNone(config)

    def test_stocks_config(self):
        """config should have STOCKS list."""
        import config
        self.assertIsInstance(config.STOCKS, list)
        self.assertIn('MSFT', config.STOCKS)


def run_tests():
    """Run all tests and return exit code."""
    loader = unittest.TestLoader()
    suite = loader.loadTestsFromModule(__import__(__name__))
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    return 0 if result.wasSuccessful() else 1


if __name__ == '__main__':
    sys.exit(run_tests())
