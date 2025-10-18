"""
MCP tool definitions for project folder management.

This module provides MCP protocol tool definitions for managing project folders
in the Alpha Vantage MCP server output system.
"""

import json
from dataclasses import asdict

import mcp.types as types

from ..utils.output_config import load_output_config
from .handler import OutputHandler


def _create_handler() -> OutputHandler:
    """Create an OutputHandler instance with loaded configuration."""
    config = load_output_config()
    return OutputHandler(config)


async def create_project_tool(project_name: str) -> str:
    """
    Create a new project folder.

    This tool creates a new project directory under the configured output root.
    Project names are automatically sanitized for security.

    Args:
        project_name: Name of the project to create.

    Returns:
        JSON string with project creation result.

    Example:
        >>> result = await create_project_tool("stock-analysis")
        >>> json.loads(result)
        {'success': True, 'project_name': 'stock-analysis', 'path': '/path/to/stock-analysis'}
    """
    handler = _create_handler()

    try:
        project_path = await handler.create_project_folder(project_name)

        return json.dumps(
            {
                "success": True,
                "project_name": project_path.name,
                "path": str(project_path),
                "message": f"Project '{project_path.name}' created successfully",
            },
            indent=2,
        )

    except Exception as e:
        return json.dumps(
            {
                "success": False,
                "error": str(e),
                "project_name": project_name,
            },
            indent=2,
        )


async def list_project_files_tool(project_name: str, pattern: str = "*") -> str:
    """
    List files in a project folder.

    This tool lists all files in a project directory, with optional pattern filtering.
    Files are sorted by modification time (newest first).

    Args:
        project_name: Name of the project.
        pattern: Glob pattern for filtering files (default: "*").

    Returns:
        JSON string with list of files and metadata.

    Example:
        >>> result = await list_project_files_tool("stock-analysis", "*.csv")
        >>> data = json.loads(result)
        >>> data['file_count']
        5
    """
    handler = _create_handler()

    try:
        files = await handler.list_project_files(project_name, pattern)

        return json.dumps(
            {
                "success": True,
                "project_name": project_name,
                "pattern": pattern,
                "file_count": len(files),
                "files": [asdict(f) for f in files],
            },
            indent=2,
        )

    except Exception as e:
        return json.dumps(
            {
                "success": False,
                "error": str(e),
                "project_name": project_name,
                "pattern": pattern,
            },
            indent=2,
        )


async def delete_file_tool(project_name: str, filename: str) -> str:
    """
    Delete a file from a project folder.

    This tool deletes a specific file from a project directory.
    Path traversal attempts are blocked for security.

    Args:
        project_name: Name of the project.
        filename: Name of the file to delete.

    Returns:
        JSON string with deletion result.

    Example:
        >>> result = await delete_file_tool("stock-analysis", "old_data.csv")
        >>> json.loads(result)
        {'success': True, 'deleted': True, 'message': 'File deleted successfully'}
    """
    handler = _create_handler()

    try:
        deleted = await handler.delete_project_file(project_name, filename)

        if deleted:
            message = f"File '{filename}' deleted successfully from project '{project_name}'"
        else:
            message = f"File '{filename}' not found in project '{project_name}'"

        return json.dumps(
            {
                "success": True,
                "deleted": deleted,
                "project_name": project_name,
                "filename": filename,
                "message": message,
            },
            indent=2,
        )

    except Exception as e:
        return json.dumps(
            {
                "success": False,
                "error": str(e),
                "project_name": project_name,
                "filename": filename,
            },
            indent=2,
        )


async def list_projects_tool() -> str:
    """
    List all project folders.

    This tool lists all project directories with metadata including
    file counts, total sizes, and last modified times.

    Returns:
        JSON string with list of projects and metadata.

    Example:
        >>> result = await list_projects_tool()
        >>> data = json.loads(result)
        >>> data['project_count']
        3
    """
    handler = _create_handler()

    try:
        projects = await handler.list_projects()

        # Calculate total stats
        total_files = sum(p.file_count for p in projects)
        total_size = sum(p.total_size for p in projects)

        return json.dumps(
            {
                "success": True,
                "project_count": len(projects),
                "total_files": total_files,
                "total_size": total_size,
                "projects": [asdict(p) for p in projects],
            },
            indent=2,
        )

    except Exception as e:
        return json.dumps(
            {
                "success": False,
                "error": str(e),
            },
            indent=2,
        )


# MCP Tool Definitions
CREATE_PROJECT_TOOL = types.Tool(
    name="create_project",
    description=(
        "Create a new project folder for organizing Alpha Vantage output files. "
        "Project names are automatically sanitized for security. "
        "This operation is idempotent - calling it multiple times with the same name is safe."
    ),
    inputSchema={
        "type": "object",
        "properties": {
            "project_name": {
                "type": "string",
                "description": "Name of the project to create (e.g., 'stock-analysis', 'portfolio-2024')",
            },
        },
        "required": ["project_name"],
    },
)

LIST_PROJECT_FILES_TOOL = types.Tool(
    name="list_project_files",
    description=(
        "List all files in a project folder with optional pattern filtering. "
        "Supports glob patterns like '*.csv', '2024-*.json', etc. "
        "Files are sorted by modification time (newest first)."
    ),
    inputSchema={
        "type": "object",
        "properties": {
            "project_name": {
                "type": "string",
                "description": "Name of the project",
            },
            "pattern": {
                "type": "string",
                "description": "Glob pattern for filtering files (default: '*' for all files)",
                "default": "*",
            },
        },
        "required": ["project_name"],
    },
)

DELETE_FILE_TOOL = types.Tool(
    name="delete_file",
    description=(
        "Delete a specific file from a project folder. "
        "Path traversal attempts are automatically blocked for security. "
        "Returns success even if file doesn't exist (idempotent)."
    ),
    inputSchema={
        "type": "object",
        "properties": {
            "project_name": {
                "type": "string",
                "description": "Name of the project",
            },
            "filename": {
                "type": "string",
                "description": "Name of the file to delete (relative to project folder)",
            },
        },
        "required": ["project_name", "filename"],
    },
)

LIST_PROJECTS_TOOL = types.Tool(
    name="list_projects",
    description=(
        "List all project folders with metadata including file counts, "
        "total sizes, and last modified times. "
        "Projects are sorted by last modified time (newest first). "
        "Hidden folders (starting with '.') are excluded."
    ),
    inputSchema={
        "type": "object",
        "properties": {},
        "required": [],
    },
)

# Export all tools and their handlers
PROJECT_MANAGEMENT_TOOLS = [
    (CREATE_PROJECT_TOOL, create_project_tool),
    (LIST_PROJECT_FILES_TOOL, list_project_files_tool),
    (DELETE_FILE_TOOL, delete_file_tool),
    (LIST_PROJECTS_TOOL, list_projects_tool),
]
