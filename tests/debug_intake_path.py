#!/usr/bin/env python3
"""
Debug script to test intake path validation exactly as the web interface does.
"""

import logging
import sys

sys.path.append("src")

# Set up logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)

from ai_research_assistant.utils.path_utils import (
    ensure_directory_exists,
    find_valid_path,
    validate_windows_path,
)


def debug_intake_validation(source_directory_input: str, output_directory_input: str):
    """Debug the exact validation logic from the intake agent."""

    print("🔍 Debug: Testing intake validation")
    print(f"Source input: '{source_directory_input}'")
    print(f"Output input: '{output_directory_input}'")
    print()

    # Step 1: Clean input (exactly as in the web interface)
    source_directory = source_directory_input.strip()
    output_directory = output_directory_input

    print(f"After strip - Source: '{source_directory}'")
    print(f"After strip - Output: '{output_directory}'")
    print()

    # Step 2: Check if empty (first validation check)
    if not source_directory:
        print("❌ FAIL: Source directory is empty")
        return False
    else:
        print("✅ PASS: Source directory is not empty")

    # Step 3: Try to find valid path variant
    print(f"🔍 Finding valid path variant for: '{source_directory}'")
    valid_source_path = find_valid_path(source_directory)

    if not valid_source_path:
        print("❌ FAIL: No valid path variant found")
        # Get detailed error message
        is_valid, error_msg = validate_windows_path(source_directory)
        print(f"   Validation error: {error_msg}")
        return False
    else:
        print(f"✅ PASS: Found valid path: '{valid_source_path}'")
        source_directory = valid_source_path

    # Step 4: Ensure output directory exists
    print(f"🔍 Ensuring output directory exists: '{output_directory}'")
    success, output_path_or_error = ensure_directory_exists(
        output_directory, create_if_missing=True
    )

    if not success:
        print(f"❌ FAIL: Output directory error: {output_path_or_error}")
        return False
    else:
        print(f"✅ PASS: Output directory ready: '{output_path_or_error}'")
        output_directory = output_path_or_error

    print()
    print("🎉 ALL VALIDATIONS PASSED!")
    print(f"Final source path: '{source_directory}'")
    print(f"Final output path: '{output_directory}'")
    return True


if __name__ == "__main__":
    # Test the exact inputs that are causing issues
    test_cases = [
        ("", "./tmp/intake_output"),  # Empty source
        ("F:\\WCBCLAIM", "./tmp/intake_output"),  # Without exclamation
        ("F:\\WCBCLAIM\\", "./tmp/intake_output"),  # With trailing backslash
        ("F:\\!WCBCLAIM", "./tmp/intake_output"),  # Correct path
        ("F:\\!WCBCLAIM\\", "./tmp/intake_output"),  # Correct path with trailing
    ]

    for i, (source, output) in enumerate(test_cases, 1):
        print(f"\n{'=' * 60}")
        print(f"TEST CASE {i}: Source='{source}', Output='{output}'")
        print("=" * 60)
        debug_intake_validation(source, output)
        print()
