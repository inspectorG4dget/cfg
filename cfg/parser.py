"""

cfg.parser
==========

This contains the ControlFlowGraph object. And will grow to contain other
things as well.

"""

import _ast
import os
import utils
import itertools
from platform import node


def parse(filename):
    """Parses the file identifed by `filename`.

    :param str filename: name of file to parse
    :returns: :class:`ControlFlowGraph`
    """
    if not (os.path.exists(filename) and os.path.isfile(filename)):
        raise CFGError('"{0}" does not exist'.format(filename))
    return ControlFlowGraph(filename)

class Node(object):
    ID = itertools.count(1)
    
    def __init__(self, node):
        self.id = self.__class__.ID.next()
        self.label = self._getLabel(node)
        self.ast = node
        self.type = utils.nodeType(self)
        self.edges = []
        
    def connect(self, node):
        dest = Node(node)
        e = Edge()
        e.source = self
        e.dest = dest
        e.setLabel()
        self.edges.append(e)
    
    def _getLabel(self, node):
        pass

class Edge(object):
    ID = itertools.count(1)
    
    def __init__(self, parent, successor):
        self.id = self.__class__.ID.next()
        self.source = parent
        self.dest = successor
        self.label = self._getLabel()
    
    def setLabel(self):
        self._getLabel()
    
    def _getLabel(self):
        pass

class CFGError(Exception):
    pass

class ControlFlowGraph(object):
    handlers = {}
    atomics = set([_ast.Add, _ast.And, _ast.Assign, _ast.AugAssign, _ast.BinOp, _ast.BitAnd, _ast.BitOr, _ast.BitXor, _ast.BoolOp, _ast.Break, _ast.Compare, _ast.Div, _ast.Eq, _ast.Expression, _ast.FloorDiv, _ast.Gt, _ast.GtE, _ast.Import, _ast.ImportFrom, _ast.In, _ast.Is, _ast.IsNot, _ast.LShift, _ast.Lt, _ast.LtE, _ast.Mod, _ast.Mult, _ast.Not, _ast.NotEq, _ast.NotIn, _ast.Or, _ast.Pass, _ast.Pow, _ast.Print, _ast.RShift, _ast.Raise, _ast.Return, _ast.Store, _ast.Str, _ast.UnaryOp, _ast.Yield])        
    
    def __init__(self, filename):
        self.filename = filename #: name of the file containing code to be analyzed
        self.ast = compile(open(filename).read(), filename, 'exec', _ast.PyCF_ONLY_AST) #: _ast.Module object
        self.functions = {} #: Dictionary of mappings from function name to _ast.FunctionDef
        self.classes = {} #: Dictionary of mappings from class name to _ast.ClassDef
        self.root = None #: Source node of type :class:`Node <Node>`. Execution begins here
        self.curr=None #: Last added node
        self.danglers = []
        self.terminals = []
        #self.generateGraph()

    def __repr__(self):
        return '<Control Flow Graph for "{0}">'.format(self.filename)

    def generateGraph(self, ast=None):
        """ Return only the root. Since the graph is fully connected, a traversal will get you anywhere you need to go """
        
        if ast is None:
            ast = self.ast
        if danglers is None:
            danglers = []
            
        for node in ast.body:
            name = utils.nodeType(node)
            node = Node(node)
            
            for d in self.danglers:
                d.connect(node)
            self.danglers = []
            self.curr = node

            # add new edge with node & update terminus
            if not self.root:
                self.root = node

            if name == 'classdef':
                self.classes[node.name] = node
            elif name == 'functiondef':
                self.functions[node.name] = node
            elif name == 'if':
                self._handleIf(node)

            self.addNode(node)

    def _handleNode(self, node, succ):
        if node.__class__ in self.atomics:
            return self._handleAtomic(node, succ)
    
    def _handleIf(self, node, succ):
        node = Node(node)
        answer = node
        succ = Node(succ)
        node.connect(succ)
        curr = Node(node.body[0])
        node.connect(curr)
        for succ in node.body[1:]:
            succ = self._handleNode(node, succ)
            curr.connect(succ)
            curr = succ
        if answer.ast.orelse.body:
            curr = answer
            for succ in curr.ast.orelse.body:
                succ = self._handleNode(curr, succ)
                curr.connect(succ)
                curr = succ
        return answer
    
    def _handleTry(self, node):
        pass
    
    def _handleRaise(self, node):
        pass
    
    def _handleFunction(self, node):
        pass
    
    def _handleLoop(self, node):
        pass
    
    def _handleAtomic(self, node, succ):
        succ = self._handleNode(succ)
        node = Node(node)
        node.connect(succ)
        return node
    
if __name__ == "__main__":
    print 'starting'
    g = ControlFlowGraph('test.py')
    g.generateGraph()
    print 'done'
