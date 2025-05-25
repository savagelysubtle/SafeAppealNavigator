"""
Path utilities for handling Windows file paths and validation.

Provides robust path validation, normalization, and validation
specifically for Windows environments.
"""

import logging
from pathlib import Path
from typing import Optional, Tuple

logger = logging.getLogger(__name__)


def normalize_windows_path(path_str: str) -> str:
    """
    Normalize a Windows path string to handle various formats.

    Args:
        path_str: Raw path string (e.g., "F:\\WCBCLAIM", "F:/WCBCLAIM")

    Returns:
        Normalized path string with proper Windows separators
    """
    if not path_str:
        return ""

    # Convert forward slashes to backslashes for Windows
    normalized = path_str.replace("/", "\\")

    # Handle UNC paths
    if normalized.startswith("\\\\"):
        return normalized

    # Ensure drive letter format (C: becomes C:\)
    if len(normalized) >= 2 and normalized[1] == ":" and not normalized.endswith("\\"):
        if len(normalized) == 2:
            normalized += "\\"
        elif normalized[2] != "\\":
            normalized = normalized[:2] + "\\" + normalized[2:]

    return normalized


def validate_windows_path(path_str: str) -> Tuple[bool, str]:
    """
    Validate if a Windows path exists and is accessible.

    Args:
        path_str: Path string to validate

    Returns:
        Tuple of (is_valid, error_message)
    """
    if not path_str or not path_str.strip():
        return False, "Path is empty"

    try:
        # Normalize the path first
        normalized_path = normalize_windows_path(path_str.strip())

        # Create Path object
        path_obj = Path(normalized_path)

        # Check if path exists
        if not path_obj.exists():
            return False, f"Path does not exist: {normalized_path}"

        # Check if it's accessible (try to list if directory)
        if path_obj.is_dir():
            try:
                # Test directory access by attempting to list
                list(path_obj.iterdir())
            except PermissionError:
                return (
                    False,
                    f"Permission denied accessing directory: {normalized_path}",
                )
            except Exception as e:
                return False, f"Error accessing directory: {e}"
        elif path_obj.is_file():
            try:
                # Test file access
                path_obj.stat()
            except PermissionError:
                return False, f"Permission denied accessing file: {normalized_path}"
            except Exception as e:
                return False, f"Error accessing file: {e}"

        return True, ""

    except Exception as e:
        logger.warning(f"Path validation error for '{path_str}': {e}")
        return False, f"Invalid path format: {e}"


def get_path_variants(path_str: str) -> list[str]:
    """
    Generate common path variants for Windows paths.

    Useful when dealing with paths that might have different formats
    (e.g., with/without exclamation marks, different separators).

    Args:
        path_str: Base path string

    Returns:
        List of possible path variants to try
    """
    if not path_str:
        return []

    variants = []
    normalized = normalize_windows_path(path_str.strip())
    variants.append(normalized)

    # Add variant without exclamation mark if present
    if "!" in normalized:
        variant_no_excl = normalized.replace("!", "")
        variants.append(variant_no_excl)

    # Add variant with exclamation mark if not present
    if "!" not in normalized and "\\" in normalized:
        parts = normalized.split("\\")
        if len(parts) >= 2:
            # Add exclamation to the last part of the drive
            parts[1] = "!" + parts[1] if not parts[1].startswith("!") else parts[1]
            variant_with_excl = "\\".join(parts)
            variants.append(variant_with_excl)

    # Remove duplicates while preserving order
    unique_variants = []
    for variant in variants:
        if variant not in unique_variants:
            unique_variants.append(variant)

    return unique_variants


def find_valid_path(path_str: str) -> Optional[str]:
    """
    Find the first valid path from common variants.

    Args:
        path_str: Base path string

    Returns:
        First valid path found, or None if none exist
    """
    variants = get_path_variants(path_str)

    for variant in variants:
        is_valid, _ = validate_windows_path(variant)
        if is_valid:
            logger.info(f"Found valid path variant: {variant}")
            return variant

    logger.warning(f"No valid path variants found for: {path_str}")
    return None


def ensure_directory_exists(
    path_str: str, create_if_missing: bool = True
) -> Tuple[bool, str]:
    """
    Ensure a directory exists, optionally creating it.

    Args:
        path_str: Directory path string
        create_if_missing: Whether to create the directory if it doesn't exist

    Returns:
        Tuple of (success, path_or_error_message)
    """
    try:
        normalized_path = normalize_windows_path(path_str.strip())
        path_obj = Path(normalized_path)

        if path_obj.exists():
            if path_obj.is_dir():
                return True, normalized_path
            else:
                return False, f"Path exists but is not a directory: {normalized_path}"

        if create_if_missing:
            path_obj.mkdir(parents=True, exist_ok=True)
            logger.info(f"Created directory: {normalized_path}")
            return True, normalized_path
        else:
            return False, f"Directory does not exist: {normalized_path}"

    except Exception as e:
        logger.error(f"Error ensuring directory exists '{path_str}': {e}")
        return False, f"Error creating directory: {e}"
