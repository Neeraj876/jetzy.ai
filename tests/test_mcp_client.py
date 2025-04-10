import pytest
import json
import asyncio

from unittest.mock import patch, MagicMock, AsyncMock
import os
import sys

from mcp_client import (
    llm_client,
    get_prompt_to_identify_tool_and_arguments,
    run_async,
    run_tool_query
)