"""File utility functions for consistent path resolution.

This module provides shared utilities for resolving file paths across
the application, ensuring consistency between upload, download, deletion,
and audit pack generation.
"""

import os
from typing import Optional


# Backend directory (tracehub/backend/)
BACKEND_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def get_full_path(file_path: Optional[str]) -> Optional[str]:
    """Resolve a document file path to an absolute path.

    Args:
        file_path: The file path stored in the database. Can be:
            - Absolute path (returned as-is)
            - Relative path starting with "./" (resolved relative to backend dir)
            - Relative path without "./" (resolved relative to backend dir)

    Returns:
        Absolute path to the file, or None if file_path is None/empty.

    Example:
        >>> get_full_path("./uploads/abc-123/doc.pdf")
        "/path/to/tracehub/backend/uploads/abc-123/doc.pdf"

        >>> get_full_path("/absolute/path/doc.pdf")
        "/absolute/path/doc.pdf"
    """
    if not file_path:
        return None

    # Already absolute path
    if os.path.isabs(file_path):
        return file_path

    # Relative paths are relative to backend working directory
    return os.path.join(BACKEND_DIR, file_path)


def file_exists(file_path: Optional[str]) -> bool:
    """Check if a document file exists on disk.

    Args:
        file_path: The file path stored in the database.

    Returns:
        True if file exists, False otherwise.
    """
    full_path = get_full_path(file_path)
    if not full_path:
        return False
    return os.path.exists(full_path)


def get_file_size(file_path: Optional[str]) -> Optional[int]:
    """Get the size of a document file in bytes.

    Args:
        file_path: The file path stored in the database.

    Returns:
        File size in bytes, or None if file doesn't exist.
    """
    full_path = get_full_path(file_path)
    if not full_path or not os.path.exists(full_path):
        return None
    return os.path.getsize(full_path)


def delete_file(file_path: Optional[str]) -> bool:
    """Delete a document file from disk.

    Args:
        file_path: The file path stored in the database.

    Returns:
        True if file was deleted, False if it didn't exist.
    """
    full_path = get_full_path(file_path)
    if not full_path:
        return False

    if os.path.exists(full_path):
        os.remove(full_path)
        return True
    return False
