"""Google ADK multi-agent orchestration: one routing boss and four specialist workers."""
from __future__ import annotations
import os
from pathlib import Path
from google.adk.agents import LlmAgent
from google.adk.models.lite_llm import LiteLlm
from code_helper.config import NVIDIA_CHAT_MODEL, NVIDIA_API_KEY, PROJECT_ROOT
from code_helper.tools.rag_tools import rag_search
from code_helper.tools.project_tools import list_project_files, inspect_python_structure, get_onboarding_overview, find_text_in_codebase

if NVIDIA_API_KEY:
    os.environ["NVIDIA_NIM_API_KEY"] = NVIDIA_API_KEY
    os.environ["NVIDIA_API_KEY"] = NVIDIA_API_KEY
model = LiteLlm(model=f"nvidia_nim/{NVIDIA_CHAT_MODEL}")

# Filesystem MCP gives the Code Explainer safe read-only access to the selected codebase.
# If Node/npm or MCP dependencies are unavailable, setup instructions in README will explain the fix.
try:
    from google.adk.tools.mcp_tool import McpToolset
    from google.adk.tools.mcp_tool.mcp_session_manager import StdioConnectionParams
    from mcp import StdioServerParameters
    filesystem_tools = [
        McpToolset(
            connection_params=StdioConnectionParams(
                server_params=StdioServerParameters(
                    command="npx",
                    args=["-y", "@modelcontextprotocol/server-filesystem", str(PROJECT_ROOT)],
                ),
                timeout=30,
            ),
            tool_filter=["list_directory", "read_file"],
        )
    ]
except Exception as exc:
    # The other workers remain importable, but the Code Explainer will report this setup issue.
    _mcp_error = f"{type(exc).__name__}: {exc}"
    def mcp_setup_status() -> str:
        """Report that the Filesystem MCP server could not be configured at import time."""
        return f"Filesystem MCP setup failed: {_mcp_error}. Install Node.js and verify npm/npx are on PATH."
    filesystem_tools = [mcp_setup_status]

code_searcher = LlmAgent(
    name="code_searcher",
    model=model,
    description="Finds where a feature, function, setting, or behavior is implemented in the codebase.",
    instruction=("Use rag_search for code evidence. Answer only from returned passages and name the source file(s). "
                 "If retrieval finds nothing useful, explicitly say: 'I could not find that in the indexed code.' Do not guess."),
    tools=[rag_search, find_text_in_codebase],
)

code_explainer = LlmAgent(
    name="code_explainer",
    model=model,
    description="Explains one source file in detail using the Filesystem MCP server to read the actual file.",
    instruction=("Use the Filesystem MCP read_file tool to read the requested file before explaining it. "
                 "Describe purpose, key functions/classes, inputs/outputs, and dependencies. Do not invent code that was not read. "
                 "If the file cannot be read, say so clearly."),
    tools=filesystem_tools,
)

architecture_mapper = LlmAgent(
    name="architecture_mapper",
    model=model,
    description="Maps Python files, imports, functions, classes, and relationships using static Python parsing.",
    instruction=("Use inspect_python_structure and, when helpful, list_project_files. These tools use Python AST and do not execute code. "
                 "Explain dependencies from their output only. State when a relationship cannot be established."),
    tools=[inspect_python_structure, list_project_files, find_text_in_codebase],
)

onboarding_guide = LlmAgent(
    name="onboarding_guide",
    model=model,
    description="Helps a new developer understand the project, setup steps, and a sensible first file to read.",
    instruction=("Use get_onboarding_overview and list_project_files, and use rag_search when you need implementation details. "
                 "Give a practical ordered starting path. Do not claim setup commands are verified unless the project files support them."),
    tools=[get_onboarding_overview, list_project_files, rag_search, find_text_in_codebase],
)

root_agent = LlmAgent(
    name="coordinator",
    model=model,
    description="Routes codebase questions to the correct specialist worker; it must not answer questions itself.",
    instruction=("You are a routing-only coordinator. NEVER answer the user's question directly. "
                  "Choose exactly the best specialist sub-agent: code_searcher for where/how-to-find questions; "
                  "code_explainer for explaining a named file; architecture_mapper for imports, structure, and file relationships; "
                  "onboarding_guide for first steps, setup, and project overview. Delegate to that worker and return its response. "
                  "If uncertain, choose the closest worker rather than fabricating an answer."),
    sub_agents=[code_searcher, code_explainer, architecture_mapper, onboarding_guide],
)
