"""

cfg.parser
==========

This contains the ControlFlowGraph object. And will grow to contain other
things as well.

"""

import ast
import os
from cfg.utils import nodeType


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
        #: Dictionary of mappings from function name to _ast.FunctionDef
        self.functions = {}
        #: Dictionary of mappings from class name to _ast.ClassDef
        self.classes = {}
        #: Dictionary of imports
        self.imports = {}
        #: Root node of type :class:`Node <Node>`
        self.root = None
        #: Last added node(s)
        self.termini = []
        #self.generateGraph()

    def __repr__(self):
        return '<Control Flow Grap for "{0}">'.format(self.filename)

    def generateGraph(self):
        """Generates the actual ControlFlowGraph"""
        for b in self.ast.body:
            node = Node(b)
            self.handleNode(node)

            # add new edge with node & update terminus
            if not self.root:
                self.root = node

            if not self.terminus:
                self.termini.append(node)
                continue

            self.addNode(node)

    def _handleIf(self, node):
        pass

    def _handleTry(self, node):
        pass

    def addNode(self, node):
        #for t in self.termini:
        #    t.addEdge(node)
        pass

    def handleNode(self, node):
        name = node.type

        if name == 'classdef':
            self.classes[node.id] = node
        elif name == 'functiondef':
            self.functions[node.id] = node
        elif name == 'tryexcept':
            self.handleTry(self, node)
        # need to handle if's, try-except


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
        self.type = getattr(node, '_cfg_type', nodeType(node))
        self.edges = []
        attr = self.attrs.get(self.type)
        self.id = None
        if attr:
            self.id = getattr(node, attr, None)

        if self.type == 'import':
            names = self.astNode.names
            ids = [(n.name, n.asname) for n in names]
            remove = set([None])  # items we don't want included in our tuples
            ids = [' as '.join(list(set(i) - set(remove))) for i in ids]
            self.id = ', '.join(ids)

        self.lineno = self.astNode.lineno

    def addEdge(self, node):
        self.edges.append(Edge(self, node))

    def __repr__(self):
        return '<Node [{0.type}]>'.format(self)


class Edge(object):
    def __init__(self, parent, successor):
        self.parent = parent
        self.successor = successor

    def follow(self):
        return self.successor


class CFGError(Exception):
    pass
