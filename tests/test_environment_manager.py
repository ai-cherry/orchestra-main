#!/usr/bin/env python3
"""
Tests for environment_manager.py functionality.

These tests ensure the Environment Manager works correctly for environment
switching, workspace optimization, and repository size management.
"""

import json
import os
import shutil
import tempfile
from pathlib import Path
from unittest import mock

import pytest

# Add parent directory to path to import environment_manager.py
import sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from environment_manager import EnvironmentManager, Colors


class TestEnvironmentManager:
    """Test suite for the Environment Manager functionality."""

    @pytest.fixture
    def temp_dir(self):
        """Create a temporary directory for testing."""
        temp_dir = tempfile.mkdtemp()
        yield Path(temp_dir)
        shutil.rmtree(temp_dir)

    @pytest.fixture
    def env_manager(self, temp_dir):
        """Create an environment manager with a temporary base directory."""
        return EnvironmentManager(base_dir=temp_dir)

    def setup_env_files(self, temp_dir):
        """Set up environment files for testing."""
        dev_file = temp_dir / ".env.development"
        staging_file = temp_dir / ".env.staging"
        prod_file = temp_dir / ".env.production"

        with open(dev_file, 'w') as f:
            f.write("# DEV Environment\nACTIVE=true\nAI_ORCHESTRA_ENV=dev\n")

        with open(staging_file, 'w') as f:
            f.write("# STAGING Environment\nACTIVE=false\nAI_ORCHESTRA_ENV=staging\n")

        with open(prod_file, 'w') as f:
            f.write("# PROD Environment\nACTIVE=false\nAI_ORCHESTRA_ENV=prod\n")

    def test_get_current_environment_from_indicator_file(self, env_manager, temp_dir):
        """Test environment detection from indicator files."""
        # Create a dev mode indicator file
        (temp_dir / ".dev_mode").touch()
        
        # Get current environment
        env = env_manager.get_current_environment()
        
        assert env == "dev"

    def test_get_current_environment_from_env_var(self, env_manager):
        """Test environment detection from environment variables."""
        with mock.patch.dict(os.environ, {"AI_ORCHESTRA_ENV": "staging"}):
            env = env_manager.get_current_environment()
            assert env == "staging"

    def test_get_current_environment_from_env_file(self, env_manager, temp_dir):
        """Test environment detection from .env files."""
        self.setup_env_files(temp_dir)
        
        # Get current environment
        env = env_manager.get_current_environment()
        
        assert env == "dev"  # dev is active in setup_env_files

    def test_get_current_environment_default(self, env_manager):
        """Test default environment when no indicator is present."""
        env = env_manager.get_current_environment()
        assert env == "unknown"

    def test_switch_environment(self, env_manager, temp_dir):
        """Test environment switching functionality."""
        self.setup_env_files(temp_dir)
        
        # Switch to staging
        result = env_manager.switch_environment("staging")
        
        assert result is True
        assert (temp_dir / ".staging_mode").exists()
        assert not (temp_dir / ".dev_mode").exists()
        assert not (temp_dir / ".prod_mode").exists()
        
        # Check env files were updated
        with open(temp_dir / ".env.development", 'r') as f:
            assert "ACTIVE=false" in f.read()
            
        with open(temp_dir / ".env.staging", 'r') as f:
            assert "ACTIVE=true" in f.read()
            
        # Current environment should now be staging
        assert env_manager.get_current_environment() == "staging"

    def test_switch_to_invalid_environment(self, env_manager):
        """Test switching to an invalid environment."""
        result = env_manager.switch_environment("invalid")
        assert result is False

    def test_optimize_workspace(self, env_manager, temp_dir):
        """Test workspace optimization functionality."""
        # Create a minimal settings.json
        vscode_dir = temp_dir / ".vscode"
        vscode_dir.mkdir(exist_ok=True)
        
        settings_file = vscode_dir / "settings.json"
        
        with open(settings_file, 'w') as f:
            json.dump({
                "python.linting.enabled": True
            }, f)
        
        # Run the optimizer
        env_manager.optimize_workspace()
        
        # Check that settings were updated
        with open(settings_file, 'r') as f:
            settings = json.load(f)
            
        # Verify key optimizations were applied
        assert "files.exclude" in settings
        assert "search.exclude" in settings
        assert "files.watcherExclude" in settings
        assert settings.get("search.searchOnType") is False
        assert "workbench.editor.limit.enabled" in settings

    def test_is_env_file_active(self, env_manager, temp_dir):
        """Test detection of active environment files."""
        # Create environment files
        active_env = temp_dir / "active.env"
        inactive_env = temp_dir / "inactive.env"
        
        with open(active_env, 'w') as f:
            f.write("ACTIVE=true\n")
            
        with open(inactive_env, 'w') as f:
            f.write("ACTIVE=false\n")
            
        assert env_manager._is_env_file_active(active_env) is True
        assert env_manager._is_env_file_active(inactive_env) is False
        assert env_manager._is_env_file_active(temp_dir / "nonexistent.env") is False

    @mock.patch("environment_manager.Colors.is_supported")
    def test_print_environment_banner(self, mock_is_supported, env_manager, capsys):
        """Test environment banner printing."""
        # Test with color support
        mock_is_supported.return_value = True
        env_manager._print_environment_banner("dev")
        
        captured = capsys.readouterr()
        assert "CURRENT ENVIRONMENT: DEV" in captured.out
        
        # Test without color support
        mock_is_supported.return_value = False
        env_manager._print_environment_banner("prod")
        
        captured = capsys.readouterr()
        assert "CURRENT ENVIRONMENT: PROD" in captured.out

    def test_format_size(self, env_manager):
        """Test size formatting functionality."""
        assert env_manager._format_size(512) == "512.00 B"
        assert env_manager._format_size(1024) == "1.00 KB"
        assert env_manager._format_size(1024 * 1024) == "1.00 MB"
        assert env_manager._format_size(1024 * 1024 * 1024) == "1.00 GB"
        assert env_manager._format_size(1024 * 1024 * 1024 * 1024) == "1.00 TB"

    def test_get_dir_size(self, env_manager, temp_dir):
        """Test directory size calculation."""
        # Create some files
        test_dir = temp_dir / "test_dir"
        test_dir.mkdir()
        
        # Create a few files of known size
        (test_dir / "file1.txt").write_bytes(b'0' * 1000)  # 1000 bytes
        (test_dir / "file2.txt").write_bytes(b'0' * 2000)  # 2000 bytes
        
        # Create a subdirectory with files
        subdir = test_dir / "subdir"
        subdir.mkdir()
        (subdir / "file3.txt").write_bytes(b'0' * 3000)  # 3000 bytes
        
        # Calculate size
        size = env_manager._get_dir_size(test_dir)
        
        # Should be 6000 bytes (1000 + 2000 + 3000)
        assert size == 6000

    @mock.patch("environment_manager.os.walk")
    def test_analyze_repository_size(self, mock_walk, env_manager, temp_dir):
        """Test repository size analysis."""
        # Mock os.walk to return some files
        mock_walk.return_value = [
            (str(temp_dir), [], ["file1.txt", "file2.txt"]),
            (str(temp_dir / "dir1"), [], ["file3.txt"]),
            (str(temp_dir / "dir2"), [], ["large_file.bin"]),
        ]
        
        # Mock os.path.getsize to return known sizes
        with mock.patch("os.path.getsize") as mock_getsize:
            def side_effect(path):
                if "large_file.bin" in path:
                    return 10 * 1024 * 1024  # 10 MB
                return 1024  # 1 KB for other files
                
            mock_getsize.side_effect = side_effect
            
            # Run analysis
            result = env_manager.analyze_repository_size()
            
            # Check result structure
            assert "total_size" in result
            assert "largest_files" in result
            assert "largest_dirs" in result
            
            # Total size should be 10MB + 3KB = 10,483,712 bytes
            assert result["total_size"] == 10 * 1024 * 1024 + 3 * 1024
            
            # Should have 1 large file
            assert len(result["largest_files"]) == 1
            assert "large_file.bin" in result["largest_files"][0]["path"]

    @mock.patch("pathlib.Path.glob")
    @mock.patch("pathlib.Path.unlink")
    @mock.patch("shutil.rmtree")
    def test_cleanup_repository(self, mock_rmtree, mock_unlink, mock_glob, env_manager, temp_dir):
        """Test repository cleanup functionality."""
        # Mock Path.glob to return some files and directories
        def glob_side_effect(pattern):
            if "**/__pycache__" in pattern:
                return [Path(temp_dir / "__pycache__")]
            elif "**/*.pyc" in pattern:
                return [
                    Path(temp_dir / "file1.pyc"),
                    Path(temp_dir / "file2.pyc")
                ]
            elif "**/*" in pattern and any(ext in pattern for ext in [".zip", ".tar.gz"]):
                return [Path(temp_dir / "large_archive.zip")]
            return []
            
        mock_glob.side_effect = glob_side_effect
        
        # Mock Path.is_file and Path.is_dir
        with mock.patch("pathlib.Path.is_file") as mock_is_file, \
             mock.patch("pathlib.Path.is_dir") as mock_is_dir, \
             mock.patch("pathlib.Path.stat") as mock_stat, \
             mock.patch("pathlib.Path.relative_to") as mock_relative_to:
            
            mock_is_file.side_effect = lambda: "__pycache__" not in str(mock_is_file.call_args[0][0])
            mock_is_dir.side_effect = lambda: "__pycache__" in str(mock_is_dir.call_args[0][0])
            
            # Mock stat to return size
            stat_result = mock.MagicMock()
            stat_result.st_size = 1024 * 1024  # 1 MB
            mock_stat.return_value = stat_result
            
            # Mock relative_to to return relative path
            mock_relative_to.side_effect = lambda x: Path(str(mock_relative_to.call_args[0][0]).replace(str(temp_dir), ""))
            
            # Mock _get_dir_size to return a size
            with mock.patch.object(env_manager, "_get_dir_size", return_value=5 * 1024 * 1024):
                # Run cleanup (dry run)
                result = env_manager.cleanup_repository(dry_run=True)
                
                # Check result
                assert "cleaned_size" in result
                assert "deleted_files" in result
                assert "deleted_dirs" in result
                assert "large_files" in result
                
                # Verify nothing was actually deleted (dry run)
                mock_unlink.assert_not_called()
                mock_rmtree.assert_not_called()
                
                # Run cleanup (actual deletion)
                result = env_manager.cleanup_repository(dry_run=False)
                
                # Verify files and directories were deleted
                assert mock_unlink.call_count > 0
                assert mock_rmtree.call_count > 0


if __name__ == "__main__":
    pytest.main(["-v", __file__])
