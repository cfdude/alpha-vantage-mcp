"""
Integration tests for project folder management.

Tests the complete project management workflow including:
- Creating project folders
- Listing files in projects
- Deleting files from projects
- Listing all projects
- Cross-project isolation
- Security validation
- Error handling
"""

import asyncio

import pytest

from src.output.handler import FileInfo, OutputHandler, ProjectInfo
from src.utils.output_config import OutputConfig


@pytest.fixture
def test_output_config(tmp_path, monkeypatch):
    """Create a test output configuration."""
    # Set environment variable for MCP_OUTPUT_DIR
    monkeypatch.setenv("MCP_OUTPUT_DIR", str(tmp_path))

    config = OutputConfig(
        project_name="test-project",
        enable_project_folders=True,
        output_auto=True,
        output_token_threshold=1000,
        output_csv_threshold=100,
        max_inline_rows=50,
        output_format="csv",
        output_compression=False,
        output_metadata=True,
        streaming_chunk_size=10000,
        default_folder_permissions=0o755,
    )
    return config


@pytest.fixture
def handler(test_output_config):
    """Create an OutputHandler instance for testing."""
    return OutputHandler(test_output_config)


@pytest.mark.asyncio
class TestCreateProjectFolder:
    """Tests for create_project_folder method."""

    async def test_create_project_folder_success(self, handler, test_output_config):
        """Test creating a new project folder."""
        project_path = await handler.create_project_folder("my-project")

        assert project_path.exists()
        assert project_path.is_dir()
        assert project_path.name == "my-project"
        assert project_path.parent == test_output_config.client_root

    async def test_create_project_folder_idempotent(self, handler):
        """Test that creating the same project twice is idempotent."""
        path1 = await handler.create_project_folder("test-project")
        path2 = await handler.create_project_folder("test-project")

        assert path1 == path2
        assert path1.exists()

    async def test_create_project_folder_sanitizes_name(self, handler):
        """Test that dangerous project names are sanitized."""
        # Path traversal attempt
        project_path = await handler.create_project_folder("../dangerous")
        assert project_path.name == "dangerous"
        assert ".." not in str(project_path)

        # Invalid characters
        project_path = await handler.create_project_folder("test:project?")
        assert project_path.name == "testproject"

        # Leading/trailing dots
        project_path = await handler.create_project_folder("..test..")
        assert not project_path.name.startswith(".")
        assert not project_path.name.endswith(".")

    async def test_create_project_folder_empty_name(self, handler):
        """Test that empty project names raise ValueError."""
        with pytest.raises(ValueError, match="non-empty string"):
            await handler.create_project_folder("")

        with pytest.raises(ValueError, match="non-empty string"):
            await handler.create_project_folder(None)

    async def test_create_project_folder_permissions(self, handler, test_output_config):
        """Test that project folder has correct permissions."""
        project_path = await handler.create_project_folder("perm-test")

        # Check permissions (on Unix-like systems)
        if hasattr(project_path, "stat"):
            stat_info = project_path.stat()
            mode = stat_info.st_mode & 0o777
            expected = test_output_config.default_folder_permissions
            assert mode == expected


@pytest.mark.asyncio
class TestListProjectFiles:
    """Tests for list_project_files method."""

    async def test_list_project_files_empty_project(self, handler):
        """Test listing files in an empty project."""
        await handler.create_project_folder("empty-project")
        files = await handler.list_project_files("empty-project")

        assert isinstance(files, list)
        assert len(files) == 0

    async def test_list_project_files_nonexistent_project(self, handler):
        """Test listing files in a non-existent project."""
        files = await handler.list_project_files("nonexistent")

        assert isinstance(files, list)
        assert len(files) == 0

    async def test_list_project_files_with_files(self, handler, test_output_config):
        """Test listing files in a project with multiple files."""
        # Create project and add some files
        project_path = await handler.create_project_folder("test-files")

        # Create test files
        test_files = ["data1.csv", "data2.json", "report.csv"]
        for filename in test_files:
            file_path = project_path / filename
            file_path.write_text("test content")

        # List all files
        files = await handler.list_project_files("test-files")

        assert len(files) == 3
        assert all(isinstance(f, FileInfo) for f in files)

        # Check file names
        file_names = {f.name for f in files}
        assert file_names == set(test_files)

        # Check each file has required attributes
        for file_info in files:
            assert file_info.name in test_files
            assert file_info.size > 0
            assert file_info.modified_time
            assert file_info.format in ["csv", "json"]

    async def test_list_project_files_pattern_filter(self, handler):
        """Test filtering files by glob pattern."""
        # Create project and files
        project_path = await handler.create_project_folder("pattern-test")

        files_to_create = {
            "2024-01-data.csv": "csv",
            "2024-02-data.csv": "csv",
            "2024-03-report.json": "json",
            "summary.csv": "csv",
        }

        for filename in files_to_create:
            (project_path / filename).write_text("content")

        # Test various patterns
        all_csv = await handler.list_project_files("pattern-test", "*.csv")
        assert len(all_csv) == 3
        assert all(f.format == "csv" for f in all_csv)

        jan_files = await handler.list_project_files("pattern-test", "2024-01-*")
        assert len(jan_files) == 1
        assert jan_files[0].name == "2024-01-data.csv"

        json_files = await handler.list_project_files("pattern-test", "*.json")
        assert len(json_files) == 1
        assert json_files[0].format == "json"

    async def test_list_project_files_compressed(self, handler):
        """Test listing compressed files (.csv.gz, .json.gz)."""
        project_path = await handler.create_project_folder("compressed-test")

        # Create compressed files
        (project_path / "data.csv.gz").write_text("compressed")
        (project_path / "data.json.gz").write_text("compressed")

        files = await handler.list_project_files("compressed-test")

        assert len(files) == 2

        # Check format detection
        formats = {f.format for f in files}
        assert formats == {"csv.gz", "json.gz"}

    async def test_list_project_files_sorted_by_time(self, handler):
        """Test that files are sorted by modification time (newest first)."""
        import time

        project_path = await handler.create_project_folder("sorted-test")

        # Create files with delays to ensure different mtimes
        (project_path / "old.csv").write_text("old")
        time.sleep(0.1)
        (project_path / "middle.csv").write_text("middle")
        time.sleep(0.1)
        (project_path / "new.csv").write_text("new")

        files = await handler.list_project_files("sorted-test")

        assert len(files) == 3
        # Newest should be first
        assert files[0].name == "new.csv"
        assert files[2].name == "old.csv"

    async def test_list_project_files_nested_directories(self, handler):
        """Test listing files in nested subdirectories."""
        project_path = await handler.create_project_folder("nested-test")

        # Create nested structure
        subdir = project_path / "subdir"
        subdir.mkdir()

        (project_path / "root.csv").write_text("root")
        (subdir / "nested.csv").write_text("nested")

        files = await handler.list_project_files("nested-test")

        assert len(files) == 2
        file_names = {f.name for f in files}
        assert "root.csv" in file_names
        assert "subdir/nested.csv" in file_names or "subdir\\nested.csv" in file_names

    async def test_list_project_files_invalid_project_name(self, handler):
        """Test that invalid project names raise ValueError."""
        with pytest.raises(ValueError, match="non-empty string"):
            await handler.list_project_files("")

        with pytest.raises(ValueError, match="non-empty string"):
            await handler.list_project_files(None)


@pytest.mark.asyncio
class TestDeleteProjectFile:
    """Tests for delete_project_file method."""

    async def test_delete_project_file_success(self, handler):
        """Test successfully deleting a file."""
        # Create project and file
        project_path = await handler.create_project_folder("delete-test")
        test_file = project_path / "test.csv"
        test_file.write_text("content")

        # Delete the file
        deleted = await handler.delete_project_file("delete-test", "test.csv")

        assert deleted is True
        assert not test_file.exists()

    async def test_delete_project_file_nonexistent(self, handler):
        """Test deleting a non-existent file returns False."""
        await handler.create_project_folder("delete-test")

        deleted = await handler.delete_project_file("delete-test", "missing.csv")

        assert deleted is False

    async def test_delete_project_file_compressed(self, handler):
        """Test deleting compressed files."""
        project_path = await handler.create_project_folder("delete-compressed")
        test_file = project_path / "data.csv.gz"
        test_file.write_text("compressed")

        deleted = await handler.delete_project_file("delete-compressed", "data.csv.gz")

        assert deleted is True
        assert not test_file.exists()

    async def test_delete_project_file_security_validation(self, handler):
        """Test that path traversal attempts are blocked."""
        await handler.create_project_folder("secure-delete")

        # Attempt path traversal - should be sanitized to just "other.csv"
        # The sanitize_filename will remove ".." so this should look for "other.csv"
        deleted = await handler.delete_project_file("secure-delete", "../other/file.csv")

        # Should return False because "otherfile.csv" doesn't exist
        assert deleted is False

    async def test_delete_project_file_invalid_inputs(self, handler):
        """Test that invalid inputs raise ValueError."""
        with pytest.raises(ValueError, match="non-empty string"):
            await handler.delete_project_file("", "file.csv")

        with pytest.raises(ValueError, match="non-empty string"):
            await handler.delete_project_file("project", "")

        with pytest.raises(ValueError, match="non-empty string"):
            await handler.delete_project_file(None, "file.csv")

    async def test_delete_project_file_not_a_file(self, handler):
        """Test that attempting to delete a directory raises ValueError."""
        project_path = await handler.create_project_folder("delete-dir-test")
        subdir = project_path / "subdir"
        subdir.mkdir()

        with pytest.raises(ValueError, match="not a file"):
            await handler.delete_project_file("delete-dir-test", "subdir")


@pytest.mark.asyncio
class TestListProjects:
    """Tests for list_projects method."""

    async def test_list_projects_empty(self, handler):
        """Test listing projects when none exist."""
        projects = await handler.list_projects()

        assert isinstance(projects, list)
        assert len(projects) == 0

    async def test_list_projects_with_projects(self, handler):
        """Test listing multiple projects."""
        # Create several projects
        project_names = ["project-a", "project-b", "project-c"]

        for name in project_names:
            await handler.create_project_folder(name)

        projects = await handler.list_projects()

        assert len(projects) == 3
        assert all(isinstance(p, ProjectInfo) for p in projects)

        # Check all projects are present
        listed_names = {p.name for p in projects}
        assert listed_names == set(project_names)

    async def test_list_projects_with_files(self, handler):
        """Test project metadata includes correct file counts and sizes."""
        # Create project with files
        project_path = await handler.create_project_folder("metadata-test")

        # Add files of known sizes
        (project_path / "file1.csv").write_text("x" * 100)
        (project_path / "file2.csv").write_text("y" * 200)

        projects = await handler.list_projects()

        assert len(projects) == 1
        project = projects[0]

        assert project.name == "metadata-test"
        assert project.file_count == 2
        assert project.total_size == 300  # 100 + 200
        assert project.last_modified  # Should have a timestamp

    async def test_list_projects_excludes_hidden(self, handler, test_output_config):
        """Test that hidden folders (starting with '.') are excluded."""
        # Create regular project
        await handler.create_project_folder("visible")

        # Create hidden folder directly (bypassing sanitization)
        hidden = test_output_config.client_root / ".hidden"
        hidden.mkdir()

        projects = await handler.list_projects()

        # Should only see the visible project
        assert len(projects) == 1
        assert projects[0].name == "visible"

    async def test_list_projects_sorted_by_time(self, handler):
        """Test that projects are sorted by last modified time (newest first)."""
        import time

        # Create projects with delays
        await handler.create_project_folder("old-project")
        time.sleep(0.1)
        await handler.create_project_folder("middle-project")
        time.sleep(0.1)
        await handler.create_project_folder("new-project")

        projects = await handler.list_projects()

        assert len(projects) == 3
        # Newest should be first
        assert projects[0].name == "new-project"
        assert projects[2].name == "old-project"

    async def test_list_projects_empty_project(self, handler):
        """Test that empty projects show zero files and size."""
        await handler.create_project_folder("empty")

        projects = await handler.list_projects()

        assert len(projects) == 1
        project = projects[0]

        assert project.file_count == 0
        assert project.total_size == 0
        assert project.last_modified  # Should still have a timestamp


@pytest.mark.asyncio
class TestCrossProjectScenarios:
    """Integration tests for cross-project operations."""

    async def test_multiple_projects_isolation(self, handler):
        """Test that files in different projects are isolated."""
        # Create two projects with same-named files
        project1_path = await handler.create_project_folder("project1")
        project2_path = await handler.create_project_folder("project2")

        (project1_path / "data.csv").write_text("project1 data")
        (project2_path / "data.csv").write_text("project2 data")

        # List files in each project
        files1 = await handler.list_project_files("project1")
        files2 = await handler.list_project_files("project2")

        assert len(files1) == 1
        assert len(files2) == 1
        assert files1[0].name == "data.csv"
        assert files2[0].name == "data.csv"

        # Delete from project1 shouldn't affect project2
        deleted = await handler.delete_project_file("project1", "data.csv")
        assert deleted is True

        # Project2 file should still exist
        files2_after = await handler.list_project_files("project2")
        assert len(files2_after) == 1

    async def test_complete_workflow(self, handler):
        """Test complete workflow: create, add files, list, delete, verify."""
        # 1. Create project
        project_path = await handler.create_project_folder("workflow-test")
        assert project_path.exists()

        # 2. Add files
        test_files = {
            "daily-2024-01.csv": "csv data",
            "weekly-2024.json": "json data",
            "report.csv.gz": "compressed",
        }

        for filename, content in test_files.items():
            (project_path / filename).write_text(content)

        # 3. List all projects
        all_projects = await handler.list_projects()
        assert any(p.name == "workflow-test" for p in all_projects)

        workflow_project = next(p for p in all_projects if p.name == "workflow-test")
        assert workflow_project.file_count == 3

        # 4. List files in project
        files = await handler.list_project_files("workflow-test")
        assert len(files) == 3

        # 5. Filter by pattern
        csv_files = await handler.list_project_files("workflow-test", "*.csv")
        assert len(csv_files) == 1

        # 6. Delete a file
        deleted = await handler.delete_project_file("workflow-test", "daily-2024-01.csv")
        assert deleted is True

        # 7. Verify deletion
        files_after = await handler.list_project_files("workflow-test")
        assert len(files_after) == 2
        assert not any(f.name == "daily-2024-01.csv" for f in files_after)

        # 8. Verify project stats updated
        all_projects_after = await handler.list_projects()
        workflow_project_after = next(p for p in all_projects_after if p.name == "workflow-test")
        assert workflow_project_after.file_count == 2


@pytest.mark.asyncio
class TestErrorHandling:
    """Tests for error handling in project management."""

    async def test_list_files_not_a_directory(self, handler, test_output_config):
        """Test listing files when path exists but is not a directory."""
        # Create a file instead of directory
        file_path = test_output_config.client_root / "not-a-dir"
        file_path.write_text("content")

        with pytest.raises(ValueError, match="not a directory"):
            await handler.list_project_files("not-a-dir")

    async def test_concurrent_operations(self, handler):
        """Test that concurrent operations don't interfere with each other."""
        # Create project
        await handler.create_project_folder("concurrent-test")

        # Define operations
        async def create_file(filename):
            project_path = handler.config.client_root / "concurrent-test"
            (project_path / filename).write_text("content")

        async def list_files():
            return await handler.list_project_files("concurrent-test")

        # Run operations concurrently
        await asyncio.gather(
            create_file("file1.csv"),
            create_file("file2.csv"),
            create_file("file3.csv"),
            list_files(),
            list_files(),
        )

        # Verify all files were created
        final_files = await handler.list_project_files("concurrent-test")
        assert len(final_files) == 3


@pytest.mark.asyncio
class TestMCPToolIntegration:
    """Tests for MCP tool integration."""

    async def test_import_project_tools(self):
        """Test that project tools can be imported."""
        from src.output.project_tools import (
            CREATE_PROJECT_TOOL,
            DELETE_FILE_TOOL,
            LIST_PROJECT_FILES_TOOL,
            LIST_PROJECTS_TOOL,
            PROJECT_MANAGEMENT_TOOLS,
        )

        # Verify tool definitions exist
        assert CREATE_PROJECT_TOOL.name == "create_project"
        assert LIST_PROJECT_FILES_TOOL.name == "list_project_files"
        assert DELETE_FILE_TOOL.name == "delete_file"
        assert LIST_PROJECTS_TOOL.name == "list_projects"

        # Verify tools list
        assert len(PROJECT_MANAGEMENT_TOOLS) == 4

    async def test_tool_execution(self, handler, test_output_config, monkeypatch):
        """Test that MCP tools can execute successfully."""
        import json

        from src.output.project_tools import (
            create_project_tool,
            delete_file_tool,
            list_project_files_tool,
            list_projects_tool,
        )

        # Mock the config loader to return our test config
        def mock_load_config():
            return test_output_config

        monkeypatch.setattr("src.output.project_tools.load_output_config", mock_load_config)

        # Test create_project
        result = await create_project_tool("test-mcp")
        data = json.loads(result)
        assert data["success"] is True
        assert data["project_name"] == "test-mcp"

        # Test list_projects
        result = await list_projects_tool()
        data = json.loads(result)
        assert data["success"] is True
        assert data["project_count"] >= 1

        # Create a file for testing
        project_path = test_output_config.client_root / "test-mcp"
        (project_path / "test.csv").write_text("content")

        # Test list_project_files
        result = await list_project_files_tool("test-mcp")
        data = json.loads(result)
        assert data["success"] is True
        assert data["file_count"] == 1

        # Test delete_file
        result = await delete_file_tool("test-mcp", "test.csv")
        data = json.loads(result)
        assert data["success"] is True
        assert data["deleted"] is True

        # Test delete_file on non-existent file
        result = await delete_file_tool("test-mcp", "missing.csv")
        data = json.loads(result)
        assert data["success"] is True
        assert data["deleted"] is False

    async def test_tool_error_handling(self, test_output_config, monkeypatch):
        """Test that MCP tools handle errors gracefully."""
        import json

        from src.output.project_tools import (
            create_project_tool,
            delete_file_tool,
            list_project_files_tool,
        )

        # Mock the config loader to return our test config
        def mock_load_config():
            return test_output_config

        monkeypatch.setattr("src.output.project_tools.load_output_config", mock_load_config)

        # Test create_project with invalid name
        result = await create_project_tool("")
        data = json.loads(result)
        assert data["success"] is False
        assert "error" in data

        # Test list_project_files with invalid name
        result = await list_project_files_tool("")
        data = json.loads(result)
        assert data["success"] is False
        assert "error" in data

        # Test delete_file with invalid name
        result = await delete_file_tool("", "file.csv")
        data = json.loads(result)
        assert data["success"] is False
        assert "error" in data
