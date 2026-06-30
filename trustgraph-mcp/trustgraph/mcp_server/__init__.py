def run():
    from .mcp import run as run_server

    return run_server()


__all__ = ["run"]
