# The code in this module is mostly borrowed/adapted from PyScaffold and was originally
# published under the MIT license
# The original PyScaffold license can be found in 'NOTICE.txt'
"""
.. _entry point: https://setuptools.readthedocs.io/en/latest/userguide/entry_point.html
"""

import sys
from textwrap import dedent
from typing import Callable, Iterable, List, Optional

from .. import __version__
from ..types import Plugin

if sys.version_info[:2] >= (3, 8):  # pragma: no cover
    # TODO: Import directly (no need for conditional) when `python_requires = >= 3.8`
    from importlib.metadata import EntryPoint, entry_points
else:  # pragma: no cover
    from importlib_metadata import EntryPoint, entry_points


ENTRYPOINT_GROUP = "validate_pyproject.tool_validator"


def iterate_entry_points(group=ENTRYPOINT_GROUP) -> Iterable[EntryPoint]:
    """Produces a generator yielding an EntryPoint object for each plugin registered
    via ``setuptools`` `entry point`_ mechanism.

    This method can be used in conjunction with :obj:`load_from_entry_point` to filter
    the plugins before actually loading them.
    """  # noqa
    entries = entry_points()
    if hasattr(entries, "select"):
        # The select method was introduced in importlib_metadata 3.9 (and Python 3.10)
        # and the previous dict interface was declared deprecated
        entries_ = entries.select(group=group)  # type: ignore
    else:
        # TODO: Once Python 3.10 becomes the oldest version supported, this fallback and
        #       conditional statement can be removed.
        entries_ = (plugin for plugin in entries.get(group, []))
    return sorted(entries_, key=lambda e: e.name)


def load_from_entry_point(entry_point: EntryPoint) -> Plugin:
    """Carefully load the plugin, raising a meaningful message in case of errors"""
    try:
        cls = entry_point.load()
        return cls()
    except Exception as ex:
        raise ErrorLoadingPlugin(entry_point=entry_point) from ex


def list_from_entry_points(
    group: str = ENTRYPOINT_GROUP,
    filtering: Callable[[EntryPoint], bool] = lambda _: True,
) -> List[Plugin]:
    """Produces a list of plugin objects for each plugin registered
    via ``setuptools`` `entry point`_ mechanism.

    Args:
        group: name of the setuptools' entry point group where plugins is being
            registered
        filtering: function returning a boolean deciding if the entry point should be
            loaded and included (or not) in the final list. A ``True`` return means the
            plugin should be included.
    """  # noqa
    return [
        load_from_entry_point(e) for e in iterate_entry_points(group) if filtering(e)
    ]


class ErrorLoadingPlugin(RuntimeError):
    """There was an error loading '{plugin}'.
    Please make sure you have installed a version of the plugin that is compatible
    with {package} {version}. You can also try uninstalling it.
    """

    def __init__(self, plugin: str = "", entry_point: Optional[EntryPoint] = None):
        if entry_point and not plugin:
            plugin = getattr(entry_point, "module", entry_point.name)

        sub = dict(package=__package__, version=__version__, plugin=plugin)
        msg = dedent(self.__doc__ or "").format(**sub).splitlines()
        super().__init__(f"{msg[0]}\n{' '.join(msg[1:])}")