"""Pytest configuration for backend tests."""

import pytest

# Ignore scripts directory during test collection
collect_ignore = ["scripts"]


def pytest_ignore_collect(collection_path, config):
    """Ignore the scripts directory during test collection."""
    if "scripts" in str(collection_path):
        return True
    return False
