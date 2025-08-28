import pkgutil

import src.video_edit_mcp.editorpy.image.fx as fx

__all__ = [name for _, name, _ in pkgutil.iter_modules(
    fx.__path__) if name != "all"]

for name in __all__:
    exec("from ..%s import %s" % (name, name))
