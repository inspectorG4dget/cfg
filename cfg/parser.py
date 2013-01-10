"""

cfg.parser
==========

This contains the ControlFlowGraph object. And will grow to contain other
things as well.

"""

import ast
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
        self.ast = ast.parse(open(filename).read(), filename)
        #self.ast = compile(open(filename).read(), filename, 'exec',
        #                   _ast.PyCF_ONLY_AST)
        #: Dictionary of mappings from function name to _ast.FunctionDef
        self.functions = {}
        #: Dictionary of mappings from class name to _ast.ClassDef
        self.classes = {}
        #: Root node of type :class:`Node <Node>`
        self.root = None
        #: Last added node
        self.terminus = None
        #self.generateGraph()

    def __repr__(self):
        return '<Control Flow Grap for "{0}">'.format(self.filename)

    def generateGraph(self):
        """Generates the actual ControlFlowGraph"""
        for node in self.ast.body:
            name = node_type(node)

            pathNode = Node(node)

            if name == 'classdef':
                self.classes[node.name] = pathNode
            elif name == 'functiondef':
                self.functions[node.name] = pathNode
            elif name == 'if':
                self._handleIf(pathNode)

            # add new edge with node & update terminus
            if not self.root:
                self.root = pathNode

            if not self.terminus:
                self.terminus = pathNode
                continue

            self.addNode(pathNode)

    def _handleIf(self, node):
        pass

    def addNode(self, node):
        """Adds a node to the terminus and modifies the terminus"""
        self.terminus.addEdge(node)
        self.terminus = pathNode


class Node(object):
    attrs = {
        'str': 's',
        'int': 'n',
        'expr': 'value',
        'fucnctiondef': 'name',
        'classdef': 'name',
    }
    def __init__(self, node):
        self.astNode = node
        self.type = node._cfg_type
        self.edges = []
        attr = self.attrs.get(self.type)
        self.id = None
        if attr:
            self.id = getattr(node, attr, None)

    def addEdge(node):
        self.edges.append(Edge(self, node))


class Edge(object):
    def __init__(self, parent, successor):
        self.parent = parent
        self.successor = successor

    def follow(self):
        return self.successor


class CFGError(Exception):
    pass
