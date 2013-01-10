"""

cfg.parser
==========

This contains the ControlFlowGraph object. And will grow to contain other
things as well.

"""

import _ast
#import ast
import os
from cfg.utils import node_type


def parse(filename):
    """Parses the file identifed by `filename`.

    :param str filename: name of file to parse
    :returns: :class:`ControlFlowGraph`
    """
    if not (os.path.exists(filename) and os.path.isfile(filename)):
        raise CFGError('"{0}" does not exist'.format(filename))
    return ControlFlowGraph(filename)


class ControlFlowGraph(object):
    def __init__(self, filename):
        #: Name of the file
        self.filename = filename
        #: _ast.Module object
        self.ast = compile(open(filename).read(), filename, 'exec',
                           _ast.PyCF_ONLY_AST)
        #: Dictionary of mappings from function name to _ast.FunctionDef
        self.functions = {}
        #: Dictionary of mappings from class name to _ast.ClassDef
        self.classes = {}
        #: Root node of type :class:`Node <Node>`
        self.root = None
        #: Last added node
        self.terminus = None
        #self.generate_graph()

    def __repr__(self):
        return '<Control Flow Grap for "{0}">'.format(self.filename)

    def generate_graph(self):
        for node in self.ast.body:
            name = node_type(node)

            if not self.root:
                self.root = Node(node)

            if not self.terminus:
                self.terminus = self.root

            if name == 'classdef':
                self.classes[node.name] = node
            elif name == 'functiondef':
                self.functions[node.name] = node
            elif name == 'if':
                self._handle_if(node)

            # add new edge with node & update terminus

    def _handle_if(self, node):
        pass


class Node(object):
    def __init__(self, node):
        self.node = node
        self.type = node._cfg_type
        self.edge = None


class Edge(object):
    def __init__(self, parent, successor):
        self.parent
        self.successor


class CFGError(Exception):
    pass
