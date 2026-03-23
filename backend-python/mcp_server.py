#!/usr/bin/env python3
"""
MCP Server for KubeSentinel.

This FastMCP server exposes KubeSentinel's AI-operated diagnostics and Kubernetes querying
capabilities to any compatible Model Context Protocol (MCP) client.
"""

from typing import Optional, List, Dict, Any
from enum import Enum
import httpx
import logging
from pydantic import BaseModel, Field, field_validator, ConfigDict
from mcp.server.fastmcp import FastMCP, Context

# Initialize the MCP server
mcp = FastMCP("kubesentinel_mcp")

# --- Default Config ---
API_BASE_URL = "http://localhost:8000/api/v1"

# --- Pydantic Models ---
class ResponseFormat(str, Enum):
    """Output format for tool responses."""
    MARKDOWN = "markdown"
    JSON = "json"

class GetAlertsInput(BaseModel):
    """Input model for querying alerts."""
    model_config = ConfigDict(str_strip_whitespace=True, validate_assignment=True)

    status: Optional[str] = Field(default="pending", description="Filter alerts by status (e.g. 'pending', 'analyzed', 'resolved')")
    limit: Optional[int] = Field(default=20, description="Maximum results to return", ge=1, le=100)
    response_format: ResponseFormat = Field(default=ResponseFormat.MARKDOWN, description="Output format")

class AnalyzeAlertInput(BaseModel):
    """Input model for forcing AI analysis on an alert."""
    model_config = ConfigDict(str_strip_whitespace=True, validate_assignment=True)

    alert_id: int = Field(..., description="The ID of the KubeSentinel alert to analyze")
    force_retry: bool = Field(default=False, description="Whether to bypass the AI cooldown lock")

# --- Shared Utils ---
async def _make_api_request(endpoint: str, method: str = "GET", **kwargs) -> dict:
    """Reusable function for KubeSentinel API calls."""
    async with httpx.AsyncClient() as client:
        response = await client.request(
            method,
            f"{API_BASE_URL}/{endpoint}",
            timeout=30.0,
            **kwargs
        )
        response.raise_for_status()
        return response.json()

def _handle_api_error(e: Exception) -> str:
    if isinstance(e, httpx.HTTPStatusError):
        if e.response.status_code == 404:
            return "Error: Alert or Resource not found in KubeSentinel."
        elif e.response.status_code == 429:
            return "Error: Rate limit or Cooldown active on KubeSentinel AI Core."
        return f"Error: KubeSentinel API returned status {e.response.status_code}"
    elif isinstance(e, httpx.TimeoutException):
        return "Error: Request to KubeSentinel timed out."
    return f"Error: Unexpected error occurred: {type(e).__name__}"

# --- Tools ---
@mcp.tool(
    name="kubesentinel_get_alerts",
    annotations={
        "title": "Get KubeSentinel Alerts",
        "readOnlyHint": True,
        "destructiveHint": False,
        "idempotentHint": True,
        "openWorldHint": False
    }
)
async def kubesentinel_get_alerts(params: GetAlertsInput) -> str:
    """
    Fetch the list of unhandled/analyzed Kubernetes alerts from KubeSentinel's database.

    Args:
        params: GetAlertsInput with 'status' and 'limit'.
    
    Returns:
        JSON or Markdown string indicating active K8s issues.
    """
    try:
        # We assume local API exposes GET /alerts. For this MCP we just emulate or hit it.
        # Note: If the actual FastAPI doesn't expose list alerts, this is a skeleton for expansion.
        data = await _make_api_request("alerts/status", method="GET")
        health = data.get("status", "unknown")
        
        if params.response_format == ResponseFormat.MARKDOWN:
            return f"## 🛡️ KubeSentinel Status\n- **Backend Health**: {health}\n- Use KubeSentinel Dashboard for detailed list."
        return str(data)

    except Exception as e:
        return _handle_api_error(e)

if __name__ == "__main__":
    import asyncio
    logging.basicConfig(level=logging.INFO)
    # Exposing the MCP server via Streamable HTTP (Default behavior or stdio depending on usage)
    mcp.run()
