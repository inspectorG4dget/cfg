"""

cfg.utils
=========

Various utilities for cfg

"""


def nodeType(node):
    if hasattr(node, '_cfg_type'):
        return node._cfg_type

    name = node.__class__.__name__.lower()
    node._cfg_type = name
    return name


def flattenList(L):
    if not L: return L
    e = L[0]
    if not isinstance(e, list): return [e] + flattenList(L[1:])
    return flattenList(e) + flattenList(L[1:])

