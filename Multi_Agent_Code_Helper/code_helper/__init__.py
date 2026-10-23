"""Multi-Agent Code Helper package.

Agent loading is left lazy so the one-time indexing command does not start the
ADK agents or the Filesystem MCP process as an import side effect.
"""

def __getattr__(name):
    if name == "root_agent":
        from .agent import root_agent
        return root_agent
    raise AttributeError(name)
