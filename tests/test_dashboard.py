"""
SRCC Regression Tests
End-to-end tests to verify dashboard components load correctly.
Run with: python3 -m pytest tests/test_dashboard.py -v
Or manually: python3 tests/test_dashboard.py
"""

import requests
import sys
import os

BASE_URL = "http://localhost:80"

# Key endpoints that must work
ENDPOINTS = [
    ("/", "Main dashboard HTML"),
    ("/stats", "System stats (cpu, memory, uptime, last_tend_time)"),
    ("/stocks", "Stock prices"),
    ("/weather", "Weather data"),
    ("/digest", "News digest"),
    ("/ai-digest", "AI digest with headlines"),
    ("/journal", "Journal entries"),
    ("/life", "Life metrics"),
    ("/life/streaks", "Fitness streaks"),
    ("/life/mood", "Mood entries"),
    ("/life/fitness", "Fitness data"),
    ("/life/learning", "Learning data"),
    ("/life/social", "Social data"),
    ("/rancher/tasks", "Active tasks"),
    ("/chores", "Chore list"),
]

# Required fields in JSON responses
REQUIRED_FIELDS = {
    "/stats": ["cpu", "memory", "time", "uptime", "last_tend_time"],
    "/stocks": ["stocks"],
    "/weather": ["temp", "condition"],
    "/digest": ["themes"],
    "/ai-digest": ["themes", "summary"],
    "/journal": ["entries"],
    "/life": ["fitness", "mood"],
    "/life/streaks": ["fitness"],
    "/life/mood": ["entries"],
    "/life/fitness": ["workouts", "goals"],
    "/rancher/tasks": ["active_tasks"],
    "/chores": ["chores"],
}


def test_endpoint(path, description):
    """Test a single endpoint returns 200 and valid JSON (if applicable)"""
    url = BASE_URL + path
    try:
        resp = requests.get(url, timeout=10)
        if resp.status_code != 200:
            return False, f"{description}: HTTP {resp.status_code}"
        
        # Check for HTML errors in response
        if path == "/":
            # The HTML contains "Unable to load" in JS as fallback messages
            # Check for actual error indicators instead
            if "<h1>Not Found</h1>" in resp.text or "<h1>Error</h1>" in resp.text:
                return False, f"{description}: HTML contains error page"
            # Verify key dashboard sections exist
            key_sections = ['id="stocks-grid"', 'id="life-grid"', 'id="journal-card"']
            for section in key_sections:
                if section not in resp.text:
                    return False, f"{description}: Missing {section}"
        
        # Check required JSON fields
        if path in REQUIRED_FIELDS:
            try:
                data = resp.json()
                for field in REQUIRED_FIELDS[path]:
                    if field not in data:
                        return False, f"{description}: Missing field '{field}'"
            except ValueError:
                return False, f"{description}: Not valid JSON"
        
        return True, f"{description}: OK"
    except requests.exceptions.ConnectionError:
        return False, f"{description}: Connection refused (is server running?)"
    except Exception as e:
        return False, f"{description}: {e}"


def run_tests():
    """Run all tests and report results"""
    print("=" * 60)
    print("SRCC Regression Tests")
    print("=" * 60)
    
    passed = 0
    failed = 0
    
    for path, description in ENDPOINTS:
        ok, msg = test_endpoint(path, description)
        status = "✓" if ok else "✗"
        print(f"{status} {msg}")
        if ok:
            passed += 1
        else:
            failed += 1
    
    print("=" * 60)
    print(f"Results: {passed} passed, {failed} failed")
    print("=" * 60)
    
    return failed == 0


if __name__ == "__main__":
    success = run_tests()
    sys.exit(0 if success else 1)
