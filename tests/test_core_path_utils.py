"""
Test suite for core.path_utils module.

This module contains comprehensive tests for Windows path handling utilities,
including path normalization, validation, variant generation, and directory
management functionality.
"""

from unittest.mock import Mock, patch

import pytest

from ai_research_assistant.core.path_utils import (
    ensure_directory_exists,
    find_valid_path,
    get_path_variants,
    normalize_windows_path,
    validate_windows_path,
)


class TestNormalizeWindowsPath:
    """Test cases for normalize_windows_path function."""

    def test_normalize_empty_path(self):
        """Test normalizing empty path."""
        result = normalize_windows_path("")
        assert result == ""

    def test_normalize_none_path(self):
        """Test normalizing None path."""
        result = normalize_windows_path(None)
        assert result == ""

    def test_normalize_forward_slashes_to_backslashes(self):
        """Test conversion of forward slashes to backslashes."""
        test_cases = [
            ("C:/Users/Test", "C:\\Users\\Test"),
            ("F:/WCBCLAIM/documents", "F:\\WCBCLAIM\\documents"),
            ("C:/Program Files/App", "C:\\Program Files\\App"),
            ("/root/path", "\\root\\path"),
        ]

        for input_path, expected in test_cases:
            result = normalize_windows_path(input_path)
            assert result == expected

    def test_normalize_mixed_slashes(self):
        """Test normalization of paths with mixed slashes."""
        test_cases = [
            ("C:/Users\\Test/Documents", "C:\\Users\\Test\\Documents"),
            ("D:\\data/files\\docs", "D:\\data\\files\\docs"),
        ]

        for input_path, expected in test_cases:
            result = normalize_windows_path(input_path)
            assert result == expected

    def test_normalize_unc_paths(self):
        """Test normalization preserves UNC paths."""
        unc_paths = [
            "\\\\server\\share",
            "\\\\server\\share\\folder",
            "//server/share",  # Should convert to backslashes
        ]

        expected_results = [
            "\\\\server\\share",
            "\\\\server\\share\\folder",
            "\\\\server\\share",
        ]

        for unc_path, expected in zip(unc_paths, expected_results):
            result = normalize_windows_path(unc_path)
            assert result == expected

    def test_normalize_drive_letter_formatting(self):
        """Test proper drive letter formatting."""
        test_cases = [
            ("C:", "C:\\"),
            ("D:", "D:\\"),
            ("C:folder", "C:\\folder"),
            ("F:documents\\file.txt", "F:\\documents\\file.txt"),
            ("C:\\", "C:\\"),  # Already correct
            ("C:\\Users", "C:\\Users"),  # Already correct
        ]

        for input_path, expected in test_cases:
            result = normalize_windows_path(input_path)
            assert result == expected

    def test_normalize_relative_paths(self):
        """Test normalization of relative paths."""
        test_cases = [
            ("folder/subfolder", "folder\\subfolder"),
            ("./current/folder", ".\\current\\folder"),
            ("../parent/folder", "..\\parent\\folder"),
        ]

        for input_path, expected in test_cases:
            result = normalize_windows_path(input_path)
            assert result == expected


class TestValidateWindowsPath:
    """Test cases for validate_windows_path function."""

    def test_validate_empty_path(self):
        """Test validation of empty path."""
        is_valid, error_msg = validate_windows_path("")
        assert is_valid is False
        assert "empty" in error_msg.lower()

    def test_validate_whitespace_path(self):
        """Test validation of whitespace-only path."""
        is_valid, error_msg = validate_windows_path("   ")
        assert is_valid is False
        assert "empty" in error_msg.lower()

    @patch("ai_research_assistant.core.path_utils.Path")
    def test_validate_existing_file(self, mock_path_class):
        """Test validation of existing file."""
        # Setup mock
        mock_path = Mock()
        mock_path.exists.return_value = True
        mock_path.is_dir.return_value = False
        mock_path.is_file.return_value = True
        mock_path.stat.return_value = Mock()  # Successful stat call
        mock_path_class.return_value = mock_path

        is_valid, error_msg = validate_windows_path("C:\\test\\file.txt")
        assert is_valid is True
        assert error_msg == ""

    @patch("ai_research_assistant.core.path_utils.Path")
    def test_validate_existing_directory(self, mock_path_class):
        """Test validation of existing directory."""
        # Setup mock
        mock_path = Mock()
        mock_path.exists.return_value = True
        mock_path.is_dir.return_value = True
        mock_path.iterdir.return_value = iter([])  # Empty directory
        mock_path_class.return_value = mock_path

        is_valid, error_msg = validate_windows_path("C:\\test\\folder")
        assert is_valid is True
        assert error_msg == ""

    @patch("ai_research_assistant.core.path_utils.Path")
    def test_validate_nonexistent_path(self, mock_path_class):
        """Test validation of nonexistent path."""
        # Setup mock
        mock_path = Mock()
        mock_path.exists.return_value = False
        mock_path_class.return_value = mock_path

        is_valid, error_msg = validate_windows_path("C:\\nonexistent\\path")
        assert is_valid is False
        assert "does not exist" in error_msg

    @patch("ai_research_assistant.core.path_utils.Path")
    def test_validate_permission_denied_directory(self, mock_path_class):
        """Test validation with permission denied on directory."""
        # Setup mock
        mock_path = Mock()
        mock_path.exists.return_value = True
        mock_path.is_dir.return_value = True
        mock_path.iterdir.side_effect = PermissionError("Access denied")
        mock_path_class.return_value = mock_path

        is_valid, error_msg = validate_windows_path("C:\\restricted\\folder")
        assert is_valid is False
        assert "Permission denied" in error_msg

    @patch("ai_research_assistant.core.path_utils.Path")
    def test_validate_permission_denied_file(self, mock_path_class):
        """Test validation with permission denied on file."""
        # Setup mock
        mock_path = Mock()
        mock_path.exists.return_value = True
        mock_path.is_dir.return_value = False
        mock_path.is_file.return_value = True
        mock_path.stat.side_effect = PermissionError("Access denied")
        mock_path_class.return_value = mock_path

        is_valid, error_msg = validate_windows_path("C:\\restricted\\file.txt")
        assert is_valid is False
        assert "Permission denied" in error_msg

    @patch("ai_research_assistant.core.path_utils.Path")
    def test_validate_invalid_path_format(self, mock_path_class):
        """Test validation with invalid path format."""
        # Setup mock to raise exception on Path creation
        mock_path_class.side_effect = ValueError("Invalid path")

        is_valid, error_msg = validate_windows_path("C:\\invalid\\<>path")
        assert is_valid is False
        assert "Invalid path format" in error_msg

    @patch("ai_research_assistant.core.path_utils.Path")
    def test_validate_other_directory_error(self, mock_path_class):
        """Test validation with other directory access errors."""
        # Setup mock
        mock_path = Mock()
        mock_path.exists.return_value = True
        mock_path.is_dir.return_value = True
        mock_path.iterdir.side_effect = OSError("Disk error")
        mock_path_class.return_value = mock_path

        is_valid, error_msg = validate_windows_path("C:\\test\\folder")
        assert is_valid is False
        assert "Error accessing directory" in error_msg


class TestGetPathVariants:
    """Test cases for get_path_variants function."""

    def test_get_variants_empty_path(self):
        """Test getting variants for empty path."""
        variants = get_path_variants("")
        assert variants == []

    def test_get_variants_basic_path(self):
        """Test getting variants for basic path."""
        variants = get_path_variants("C:\\test\\folder")
        assert "C:\\test\\folder" in variants
        assert len(variants) >= 1

    def test_get_variants_path_with_exclamation(self):
        """Test getting variants for path with exclamation mark."""
        variants = get_path_variants("F:\\!WCBCLAIM\\documents")

        # Should include original path
        assert "F:\\!WCBCLAIM\\documents" in variants
        # Should include variant without exclamation
        assert "F:\\WCBCLAIM\\documents" in variants

        # Should not have duplicates
        assert len(variants) == len(set(variants))

    def test_get_variants_path_without_exclamation(self):
        """Test getting variants for path without exclamation mark."""
        variants = get_path_variants("F:\\WCBCLAIM\\documents")

        # Should include original path
        assert "F:\\WCBCLAIM\\documents" in variants
        # Should include variant with exclamation
        assert "F:\\!WCBCLAIM\\documents" in variants

    def test_get_variants_removes_duplicates(self):
        """Test that variant generation removes duplicates."""
        # Path that would generate duplicate variants
        variants = get_path_variants("C:\\test")

        # Convert to set and back to list to check for duplicates
        unique_variants = list(set(variants))
        assert len(variants) == len(unique_variants)

    def test_get_variants_single_drive_letter(self):
        """Test variants for single drive letter path."""
        variants = get_path_variants("C:")
        assert "C:\\" in variants  # Normalized version

    def test_get_variants_root_path(self):
        """Test variants for root path."""
        variants = get_path_variants("\\")
        assert "\\" in variants

    def test_get_variants_preserves_order(self):
        """Test that original path comes first in variants."""
        original_path = "F:\\WCBCLAIM\\documents"
        variants = get_path_variants(original_path)

        # First variant should be the normalized original path
        normalized_original = normalize_windows_path(original_path)
        assert variants[0] == normalized_original


class TestFindValidPath:
    """Test cases for find_valid_path function."""

    @patch("ai_research_assistant.core.path_utils.validate_windows_path")
    def test_find_valid_path_first_variant_valid(self, mock_validate):
        """Test finding valid path when first variant is valid."""
        # Mock validation to return True for first call
        mock_validate.side_effect = [(True, ""), (True, "")]

        result = find_valid_path("C:\\test\\folder")
        assert result is not None
        assert "C:\\test\\folder" in result

    @patch("ai_research_assistant.core.path_utils.validate_windows_path")
    def test_find_valid_path_second_variant_valid(self, mock_validate):
        """Test finding valid path when second variant is valid."""
        # Mock validation to return False for first, True for second
        mock_validate.side_effect = [
            (False, "Not found"),
            (True, ""),
            (False, "Not found"),
        ]

        result = find_valid_path("F:\\!WCBCLAIM\\documents")
        assert result is not None

    @patch("ai_research_assistant.core.path_utils.validate_windows_path")
    def test_find_valid_path_no_valid_variants(self, mock_validate):
        """Test finding valid path when no variants are valid."""
        # Mock validation to always return False
        mock_validate.return_value = (False, "Not found")

        result = find_valid_path("C:\\nonexistent\\path")
        assert result is None

    @patch("ai_research_assistant.core.path_utils.validate_windows_path")
    def test_find_valid_path_empty_input(self, mock_validate):
        """Test finding valid path with empty input."""
        result = find_valid_path("")
        assert result is None
        # validate_windows_path should not be called for empty input
        mock_validate.assert_not_called()


class TestEnsureDirectoryExists:
    """Test cases for ensure_directory_exists function."""

    @patch("ai_research_assistant.core.path_utils.Path")
    def test_ensure_directory_exists_already_exists(self, mock_path_class):
        """Test ensuring directory exists when it already exists."""
        # Setup mock
        mock_path = Mock()
        mock_path.exists.return_value = True
        mock_path.is_dir.return_value = True
        mock_path_class.return_value = mock_path

        success, result = ensure_directory_exists("C:\\existing\\folder")
        assert success is True
        assert "C:\\existing\\folder" in result
        mock_path.mkdir.assert_not_called()

    @patch("ai_research_assistant.core.path_utils.Path")
    def test_ensure_directory_exists_is_file(self, mock_path_class):
        """Test ensuring directory exists when path is a file."""
        # Setup mock
        mock_path = Mock()
        mock_path.exists.return_value = True
        mock_path.is_dir.return_value = False
        mock_path_class.return_value = mock_path

        success, result = ensure_directory_exists("C:\\test\\file.txt")
        assert success is False
        assert "not a directory" in result

    @patch("ai_research_assistant.core.path_utils.Path")
    def test_ensure_directory_create_when_missing(self, mock_path_class):
        """Test creating directory when it doesn't exist."""
        # Setup mock
        mock_path = Mock()
        mock_path.exists.return_value = False
        mock_path.mkdir.return_value = None  # Successful creation
        mock_path_class.return_value = mock_path

        success, result = ensure_directory_exists(
            "C:\\new\\folder", create_if_missing=True
        )
        assert success is True
        assert "C:\\new\\folder" in result
        mock_path.mkdir.assert_called_once_with(parents=True, exist_ok=True)

    @patch("ai_research_assistant.core.path_utils.Path")
    def test_ensure_directory_dont_create_when_missing(self, mock_path_class):
        """Test not creating directory when it doesn't exist and create_if_missing=False."""
        # Setup mock
        mock_path = Mock()
        mock_path.exists.return_value = False
        mock_path_class.return_value = mock_path

        success, result = ensure_directory_exists(
            "C:\\missing\\folder", create_if_missing=False
        )
        assert success is False
        assert "does not exist" in result
        mock_path.mkdir.assert_not_called()

    @patch("ai_research_assistant.core.path_utils.Path")
    def test_ensure_directory_creation_fails(self, mock_path_class):
        """Test handling of directory creation failure."""
        # Setup mock
        mock_path = Mock()
        mock_path.exists.return_value = False
        mock_path.mkdir.side_effect = PermissionError("Access denied")
        mock_path_class.return_value = mock_path

        success, result = ensure_directory_exists("C:\\restricted\\folder")
        assert success is False
        assert "Error creating directory" in result

    @patch("ai_research_assistant.core.path_utils.Path")
    def test_ensure_directory_invalid_path(self, mock_path_class):
        """Test handling of invalid path during directory creation."""
        # Setup mock to raise exception
        mock_path_class.side_effect = ValueError("Invalid path")

        success, result = ensure_directory_exists("C:\\invalid\\<>path")
        assert success is False
        assert "Error creating directory" in result

    def test_ensure_directory_empty_path(self):
        """Test ensuring directory exists with empty path."""
        # Empty path normalizes to current directory, which typically exists
        success, result = ensure_directory_exists("")
        assert success is True  # Empty path refers to current directory
        assert result == ""  # Normalized empty path


class TestPathUtilsIntegration:
    """Integration tests for path utilities working together."""

    @patch("ai_research_assistant.core.path_utils.Path")
    def test_normalize_validate_integration(self, mock_path_class):
        """Test integration between normalize and validate functions."""
        # Setup mock for validation
        mock_path = Mock()
        mock_path.exists.return_value = True
        mock_path.is_dir.return_value = True
        mock_path.iterdir.return_value = iter([])
        mock_path_class.return_value = mock_path

        # Test path with forward slashes
        original_path = "C:/test/folder"
        normalized = normalize_windows_path(original_path)
        is_valid, _ = validate_windows_path(normalized)

        assert normalized == "C:\\test\\folder"
        assert is_valid is True

    @patch("ai_research_assistant.core.path_utils.validate_windows_path")
    def test_variants_find_valid_integration(self, mock_validate):
        """Test integration between get_path_variants and find_valid_path."""
        # Setup mock to make second variant valid
        mock_validate.side_effect = [
            (False, "Not found"),  # First variant invalid
            (True, ""),  # Second variant valid
        ]

        # Test path that will generate variants
        test_path = "F:\\!WCBCLAIM\\documents"
        variants = get_path_variants(test_path)
        valid_path = find_valid_path(test_path)

        assert len(variants) >= 2
        assert valid_path is not None
        assert valid_path in variants

    def test_edge_cases_comprehensive(self):
        """Test comprehensive edge cases across all functions."""
        edge_cases = [
            "",  # Empty string
            None,  # None value
            "   ",  # Whitespace
            "C:",  # Drive letter only
            "\\",  # Root backslash
            "/",  # Root forward slash
            "\\\\",  # UNC prefix
            "C:/",  # Drive with forward slash
            "relative",  # Relative path
        ]

        for case in edge_cases:
            if case is None:
                # Skip None for functions that don't handle it
                continue

            # These should not raise exceptions
            try:
                normalized = normalize_windows_path(case)
                assert isinstance(normalized, str)

                variants = get_path_variants(case)
                assert isinstance(variants, list)

                # Note: validate_windows_path and find_valid_path may fail
                # but should return proper error indicators

            except Exception as e:
                pytest.fail(f"Unexpected exception for case '{case}': {e}")


class TestLoggingAndErrorHandling:
    """Test cases for logging and error handling in path utilities."""

    @patch("ai_research_assistant.core.path_utils.Path")
    def test_logging_behavior(self, mock_path_class, caplog):
        """Test that appropriate logging occurs during operations."""
        import logging

        # Set log level to capture warnings
        caplog.set_level(logging.WARNING)

        # Mock Path constructor to raise an exception
        mock_path_class.side_effect = ValueError("Mock path error")

        # Test with any path - the mock will force an exception
        test_path = "C:\\test\\path"
        is_valid, _ = validate_windows_path(test_path)

        # Should have logged a warning about path validation error
        assert any(
            "Path validation error" in record.message for record in caplog.records
        )

    @patch("ai_research_assistant.core.path_utils.Path")
    def test_exception_handling_in_validation(self, mock_path_class):
        """Test proper exception handling in validation function."""
        # Test various exception types
        exceptions_to_test = [
            ValueError("Invalid path"),
            OSError("System error"),
            PermissionError("Access denied"),
            FileNotFoundError("File not found"),
        ]

        for exception in exceptions_to_test:
            mock_path_class.side_effect = exception

            is_valid, error_msg = validate_windows_path("C:\\test\\path")
            assert is_valid is False
            assert isinstance(error_msg, str)
            assert len(error_msg) > 0
