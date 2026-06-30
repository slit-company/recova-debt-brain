def run():
    from .mcp import run as run_server

    return run_server()


def __getattr__(name):
    if name == "McpServer":
        from .mcp import McpServer

        return McpServer
    raise AttributeError(name)


__all__ = ["run", "McpServer"]
