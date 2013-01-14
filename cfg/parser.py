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
        #: Module name
        self.module = os.path.basename(self.filename).rstrip('.py')
        #: Dictionary of mappings from function name to _ast.FunctionDef
        self.functions = {}
        #: Dictionary of mappings from class name to _ast.ClassDef
        self.classes = {}
        #: Dictionary of imports
        self.imports = {}
        #: Root node of type :class:`Node <Node>`
        self.root = None
        #: Last added node
        self.last = None
        self.generateGraph()

    def __repr__(self):
        return '<Control Flow Grap for "{0}">'.format(self.filename)

    def generateGraph(self):
        """Generates the actual ControlFlowGraph"""
        self.firstPass()

    def _handleIf(self, node):
        pass

    def _handleTry(self, node):
        pass

    def addNode(self, node):
        #for t in self.termini:
        #    t.addEdge(node)
        pass

    def firstPass(self):
        """First pass over the ast object"""
        for b in self.ast.body:
            node = Node(b, self.module)

            if node.type == 'classdef':
                self.classes[node.id] = node
            elif node.type == 'functiondef':
                self.functions[node.id] = node

            # add new edge with node & update terminus
            if not self.root:
                self.root = node

            if not self.last:
                self.last = node

            if not self.last is node:
                self.last.addEdge(node)
                self.last = node

    def secondPass(self):
        """Second pass. Uses partially constructed CFG"""
        node = self.root
        scope = [self.module]
        while True:
            if not node:
                break

            if node.hasBody and node.id:
                scope.append(node.id)

            scopeString = '.'.join(scope)
            last = None
            for child in ast.iter_child_nodes(node.astNode):
                n = Node(child, scopeString)
                if last is None:
                    node.addEdge(n)
                else:
                    last.addEdge(n)
                last = n

            node = node.edges[0].follow() if node.hasEdges else None

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

    def __init__(self, node, namespace):
        self.astNode = node
        self.type = getattr(node, '_cfg_type', nodeType(node))
        self.edges = []
        attr = self.attrs.get(self.type)
        self.id = None
        self.namespace = namespace
        if attr:
            value = getattr(node, attr, None)
            self.id = self.namespace + '.' + value

        if self.type == 'import':
            names = self.astNode.names
            ids = [(n.name, n.asname) for n in names]
            remove = set([None])  # items we don't want included in our tuples
            ids = [' as '.join(list(set(i) - set(remove))) for i in ids]
            self.id = ', '.join(ids)

        self.hasBody = True if hasattr(node, 'body') else False

        if hasattr(node, 'lineno'):
            self.lineno = self.astNode.lineno
        self.hasEdges = False

    def addEdge(self, node):
        self.hasEdges = True
        self.edges.append(Edge(self, node))

    def iterEdges(self):
        for edge in self.edges:
            yield edge

    def __repr__(self):
        return '<Node [{0.type}]>'.format(self)


class Edge(object):
    def __init__(self, parent, successor):
        self.parent = parent
        self.successor = successor

    def __repr__(self):
        return '<Edge [{0} -> {1}]>'.format(self.parent, self.successor)

    def follow(self):
        return self.successor


class CFGError(Exception):
    pass
