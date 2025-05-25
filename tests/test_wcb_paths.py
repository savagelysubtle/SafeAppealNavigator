#!/usr/bin/env python3
"""
Test script to verify WCB path validation works correctly.
"""

import sys

sys.path.append("src")

from ai_research_assistant.utils.path_utils import (
    find_valid_path,
    get_path_variants,
    normalize_windows_path,
    validate_windows_path,
)


def test_wcb_paths():
    """Test WCB path validation with both variants."""

    print("🧪 Testing WCB Path Validation\n")

    # Test paths including trailing backslashes
    test_paths = [
        "F:\\WCBCLAIM",
        "F:\\WCBCLAIM\\",  # With trailing backslash
        "F:\\!WCBCLAIM",
        "F:\\!WCBCLAIM\\",  # With trailing backslash
        "F:/WCBCLAIM",
        "F:/WCBCLAIM/",  # With trailing slash
        "F:/!WCBCLAIM",
        "F:/!WCBCLAIM/",  # With trailing slash
    ]

    for path in test_paths:
        print(f"Testing path: '{path}'")

        # Test normalization
        normalized = normalize_windows_path(path)
        print(f"  Normalized: '{normalized}'")

        # Test validation
        is_valid, error_msg = validate_windows_path(path)
        print(f"  Valid: {is_valid}")
        if not is_valid:
            print(f"  Error: {error_msg}")

        # Test variants
        variants = get_path_variants(path)
        print(f"  Variants: {variants}")

        # Test finding valid path
        valid_path = find_valid_path(path)
        print(f"  Found valid: {valid_path}")

        print()

    # Test with the automatic variant finder
    print("🔍 Testing automatic path resolution:")

    test_inputs = ["F:\\WCBCLAIM", "F:\\WCBCLAIM\\", "F:\\!WCBCLAIM", "F:\\!WCBCLAIM\\"]
    for input_path in test_inputs:
        valid_path = find_valid_path(input_path)
        print(f"Input: '{input_path}' → Valid: {valid_path}")


if __name__ == "__main__":
    test_wcb_paths()
