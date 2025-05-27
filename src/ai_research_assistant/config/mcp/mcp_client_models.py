from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class StdioConfig(BaseModel):
    """Configuration for connecting to a local MCP server via STDIO."""

    command: List[str] = Field(
        ..., description="The command and arguments to launch the server."
    )
    env: Optional[Dict[str, str]] = Field(
        default=None,
        description="Optional environment variables for the server process.",
    )


class SseConfig(BaseModel):
    """Configuration for connecting to a remote MCP server via SSE."""

    url: str = Field(..., description="The URL of the SSE endpoint for the MCP server.")


class ServerConfig(BaseModel):
    """General configuration for an MCP server connection."""

    name: str = Field(..., description="A local alias for this server connection.")
    type: str = Field(
        ..., description="The type of server connection, e.g., 'stdio' or 'sse'."
    )
    stdio_config: Optional[StdioConfig] = Field(
        default=None, description="Configuration for STDIO connections."
    )
    sse_config: Optional[SseConfig] = Field(
        default=None, description="Configuration for SSE connections."
    )
    auto_approve_tools: List[str] = Field(
        default_factory=list,
        description="List of tool names that can be executed without explicit user approval.",
    )
    disabled: bool = Field(
        default=False,
        description="If True, this server connection will not be initiated.",
    )
    timeout: int = Field(
        default=30,
        alias="timeout_seconds",
        description="Default timeout in seconds for operations with this server.",
    )

    class Config:
        extra = "ignore"  # Allows ignoring extra fields if present in config file


class McpToolSchema(BaseModel):
    """Represents the JSON schema for an MCP tool's arguments."""

    type: str = Field(
        default="object", description="The JSON schema type, typically 'object'."
    )
    properties: Optional[Dict[str, Any]] = Field(
        default_factory=dict,
        description="Schema definition for each property/argument.",
    )
    required: Optional[List[str]] = Field(
        default_factory=list, description="List of required argument names."
    )

    class Config:
        extra = "ignore"


class McpToolClientData(BaseModel):
    """Represents a discovered tool from an MCP server, enriched with client-side data."""

    name: str = Field(..., description="The name of the tool.")
    description: Optional[str] = Field(
        default=None, description="A description of what the tool does."
    )
    args_schema: McpToolSchema = Field(
        default_factory=McpToolSchema,
        description="The JSON schema for the tool's arguments.",
    )
    auto_approve: bool = Field(
        default=False,
        description="Whether this tool can be run without explicit user approval on this client.",
    )
    server_name: str = Field(
        ..., description="The name of the server this tool belongs to."
    )

    class Config:
        extra = "ignore"


class GlobalClientConfig(BaseModel):
    """Represents the global configuration for the MCP client, including all server definitions."""

    servers: List[ServerConfig] = Field(
        default_factory=list, description="A list of MCP server configurations."
    )

    class Config:
        extra = "ignore"
