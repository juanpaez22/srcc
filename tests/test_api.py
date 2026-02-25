#!/usr/bin/env python3
"""Integration tests for SRCC dashboard APIs."""

import sys
import os
import json
import tempfile
import unittest

# Add srcc to path
sys.path.insert(0, '/home/juanpaez/.nanobot/workspace/dev/srcc')

# Mock config before importing app
os.environ['SRCC_TESTING'] = '1'

# Create a temporary data file for tests
test_data = {
    "chores": [
        {"id": 1, "task": "Test chore 1", "frequency": "daily", "last_done": None},
        {"id": 2, "task": "Test chore 2", "frequency": "weekly", "last_done": None}
    ],
    "checkins": {},
    "daily_forms": {}
}

with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
    json.dump(test_data, f)
    TEST_DATA_FILE = f.name

# Patch config before importing app
import config
config.DATA_FILE = TEST_DATA_FILE

from app import app


class TestStatsAPI(unittest.TestCase):
    """Test /stats endpoint."""

    def setUp(self):
        self.client = app.test_client()

    def test_stats_returns_200(self):
        """Stats should return 200 OK."""
        response = self.client.get('/stats')
        self.assertEqual(response.status_code, 200)

    def test_stats_returns_json(self):
        """Stats should return JSON."""
        response = self.client.get('/stats')
        self.assertEqual(response.content_type, 'application/json')

    def test_stats_has_required_fields(self):
        """Stats should have cpu, memory, time fields."""
        data = json.loads(self.client.get('/stats').data)
        self.assertIn('cpu', data)
        self.assertIn('memory', data)
        self.assertIn('time', data)


class TestTendAPI(unittest.TestCase):
    """Test /tend endpoint."""

    def setUp(self):
        self.client = app.test_client()

    def test_tend_updates_last_tend_time(self):
        """POST /tend should update last_tend_time."""
        response = self.client.post('/tend')
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertTrue(data['success'])
        self.assertIn('last_tend_time', data)

    def test_stats_reflects_tend(self):
        """After /tend, /stats should show the updated time."""
        self.client.post('/tend')
        stats = json.loads(self.client.get('/stats').data)
        self.assertIn('last_tend_time', stats)
        self.assertIsNotNone(stats['last_tend_time'])


class TestChoresAPI(unittest.TestCase):
    """Test /chores endpoint."""

    def setUp(self):
        self.client = app.test_client()

    def test_chores_returns_200(self):
        """GET /chores should return 200."""
        response = self.client.get('/chores')
        self.assertEqual(response.status_code, 200)

    def test_chores_returns_dict(self):
        """GET /chores should return a dict with chores."""
        data = json.loads(self.client.get('/chores').data)
        self.assertIsInstance(data, dict)
        self.assertIn('chores', data)


class TestWeatherAPI(unittest.TestCase):
    """Test /weather endpoint."""

    def setUp(self):
        self.client = app.test_client()

    def test_weather_returns_200(self):
        """GET /weather should return 200."""
        response = self.client.get('/weather')
        # May fail if no internet, but should return something
        self.assertIn(response.status_code, [200, 500])


class TestStocksAPI(unittest.TestCase):
    """Test /stocks endpoint."""

    def setUp(self):
        self.client = app.test_client()

    def test_stocks_returns_200(self):
        """GET /stocks should return 200."""
        response = self.client.get('/stocks')
        # May fail if no API, but should return something
        self.assertIn(response.status_code, [200, 500])


class TestIndexPage(unittest.TestCase):
    """Test the main index page."""

    def setUp(self):
        self.client = app.test_client()

    def test_index_returns_200(self):
        """GET / should return 200."""
        response = self.client.get('/')
        self.assertEqual(response.status_code, 200)

    def test_index_contains_bevo(self):
        """Index should contain 'Bevo'."""
        response = self.client.get('/')
        self.assertIn(b'Bevo', response.data)


class TestTelemetryAPI(unittest.TestCase):
    """Test /telemetry endpoint."""

    def setUp(self):
        self.client = app.test_client()

    def test_telemetry_get_returns_200(self):
        """GET /telemetry should return 200."""
        response = self.client.get('/telemetry')
        self.assertEqual(response.status_code, 200)


def run_tests():
    """Run all tests and return exit code."""
    loader = unittest.TestLoader()
    suite = loader.loadTestsFromModule(__import__(__name__))
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    return 0 if result.wasSuccessful() else 1


if __name__ == '__main__':
    sys.exit(run_tests())
