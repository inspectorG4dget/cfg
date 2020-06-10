import collections
import itertools
from collections import defaultdict
from copy import deepcopy as clone

import lxml.etree as ET

from utils import flattenList


class CFG:

    BLACKLIST = set(  # a set of python's builtin functions, that are not imported or defined
                    i.strip() for i in dir(__builtins__)
               )

    LOOPS = set('for while'.split())

    def __init__(self, xmlFilePath):
        self.xml = ET.parse(xmlFilePath).getroot()
        self.nodes = set()
        self.edges = defaultdict(set)
        self.last = set([getLine(self.xml)])
        self.scopes = set()
        self.currScope = []
        self.funcstarts = {}


    def parse(self):
        self.scopes.add((0, getModuleScope(self.xml)))
        self.handleNode(self.xml)


    def removeNode(self, node):
        if node in self.nodes:
            self.nodes.pop(node)
        for src in self.edges:
            if node in self.edges[src]:
                self.edges[src].pop(node)
        if node in self.edges:
            self.edges.pop(node)

        return


    def handleNode(self, node):
        if node.tag not in self.BLACKLIST:
            curr = getLine(node)
            self.nodes.add(curr)
            delete = set()
            if curr not in self.last:
                for last in self.last:
                    self.edges[last].add(curr)
                    delete.add(last)
                self.last -= delete

            #			if node.tag != 'call' and not any(child.tag=='call' for child in node.getchildren()):
            #				self.last.add(curr)
            if node.tag != 'expr' or not any(child.tag=='call' for child in node.getchildren()):
                self.last.add(curr)
            if node.tag == "exceptElse":
                self.HANDLERS['exception'](self, node)
            else:
                self.HANDLERS[node.tag](self, node)


    def handleImportFrom(self, node):
        return 1


    def handleImport(self, node):
        return 1


    def handleReturn(self, node):
        return 1


    def handleIf(self, node):
        elseblock = node.getchildren()[-1]
        handleElse = False
        if elseblock.tag=='else' and elseblock.text != '-':
            self.edges[getLine(node)].add(getLine(elseblock.getchildren()[0]))
            node.remove(elseblock)
            handleElse = True

        for child in node.getchildren():
            self.handleNode(child)

        cache = clone(self.last)

        for child in node.getchildren():
            if getLine(child) in self.last:
                self.last.remove(getLine(child))
        self.last.add(getLine(node))

        self.scopes.add((getLine(node), getScopeEnd(node)))
        if handleElse:
            for child in elseblock.getchildren():
                self.handleNode(child)
            self.scopes.add((getLine(elseblock.getchildren()[0]), getScopeEnd(elseblock)))
            self.last.update(cache)

        self.last.add(getLastLine(node))
        if handleElse:
            node.append(elseblock)

        self.scopes.add((getLine(node), getScopeEnd(node)))


    def handleLoop(self, node):

        elseblock = node.getchildren()[-1]
        node.remove(elseblock)
        handleElse = False
        if elseblock.text != '-':
            handleElse = True
        oldLast = clone(self.last)
        if handleElse:
            self.edges[getLine(node)].add(getLine(elseblock.getchildren()[0]))
            for child in elseblock.getchildren():
                self.handleNode(child)
        self.last = oldLast

        for child in node.getchildren():
            self.handleNode(child)

        if not handleElse:
            if node.getnext() is not None:
                self.edges[getLine(node)].add(getLine(node.getnext()))

        self.handleLoopback(node)
        self.scopes.add((getLine(node), getScopeEnd(node)))
        if handleElse:
            self.last.add(getLastLine(elseblock))
            self.scopes.add((getLine(elseblock.getchildren()[0]), getScopeEnd(elseblock)))
        else:
            self.last = oldLast
            self.last.add(getLine(node))

        node.append(elseblock)


    def handleLoopback(self, node, last=None):
        """ Handle the loopback of final nodes to the looping node
            `node` does not contain an else child """

        try:
            if last is not None:
                getLine(last.getchildren()[-1])
            else:
                last = node.getchildren()[-1]
        except (IndexError, ValueError) as e:
            if last.tag != 'break':
                self.edges[getLine(last)].add(getLine(node))
            return 1

        if last.tag not in 'if tryexcept'.split():
            if last.tag != 'break':
                self.edges[getLine(last)].add(getLine(node))
                try:
                    self.last.remove(getLine(last))
                except KeyError:
                    pass
        elif last.tag == 'if':
            elseblock = last.getchildren()[-1]
            handleElse = False
            if elseblock.tag == 'else' and elseblock.text != '-':
                handleElse = True
                last.remove(elseblock)
            last = last.getchildren()[-1]
            self.handleLoopback(node, last)

            if handleElse:
                self.handleLoopback(node, elseblock.getchildren()[-1])
                node.append(elseblock)

        else: # handling a try-finally block. Leaving this as TODO for later
            pass


    def handleBreak(self, node):
        ancestor = node.getparent()
        while ancestor.tag not in self.LOOPS:
            ancestor = ancestor.getparent()

        if ancestor.getnext() is not None:
            self.edges[getLine(node)].add(getLine(getTop(ancestor.getnext())))


    def handleFunctionDef(self, node):
        #		self.funcstarts[getLine(node)] = getLine(node.getchildren()[0])
        if getLine(node) in self.last:
            self.last.remove(getLine(node))

        first = getLine(node)
        self.scopes.add((first, getScopeEnd(node)))
        self.scopes.add((getLine(node.getchildren()[0]), getScopeEnd(node)))

        for child in node.getchildren():
            self.handleNode(child)

        self.edges[getLine(node)].add(None)
        for last in self.last:
            self.edges[last].add(getLine(node))


    def handleModule(self, node):
        first = next(itertools.dropwhile(lambda n: n.tag=='functiondef', node.getchildren()))
        self.edges[0].add(getLine(first))

        self.last = set()
        fdefs = [c for c in node.getchildren() if c.tag == 'functiondef']

        for fdef in fdefs:
            self.funcstarts[getLine(fdef)] = getLine(fdef.getchildren()[0])

        for i,child in enumerate(fdefs):
            self.handleNode(child)
            #			self.edges[getLine(child)].add(None)
            self.last = set()

        for child in (c for c in node.getchildren() if c.tag != 'functiondef'):
            self.handleNode(child)

        for last in self.last:
            self.edges[last].add(None)

        return 1


    def handlePrint(self, node):
        for child in node.getchildren():
            self.handleNode(child)


    def handleCompare(self, node):
        for child in node.getchildren():
            self.handleNode(child)


    def handleBinOp(self, node):
        for child in node.getchildren():
            self.handleNode(child)


    def handleAugAssign(self, node):
        for child in node.getchildren():
            self.handleNode(child)


    def handleTry(self, node):

        tryblock = [n for n in node.getchildren() if n.tag=='expr'] # list(itertools.takewhile("expr".__eq__, node.getchildren())) # all nodes in the the try body
        elseblock = [n for n in node.getchildren() if n.tag=='exceptElse']
        handleElse = bool(elseblock)
        finallyBlock = [n for n in node.getchildren() if n.tag=='finally']

        for child in tryblock:
            self.handleNode(child)
            for sibling in (n for n in node.getchildren() if n.tag=='except' or n.tag=='exceptElse'): # all the exceptions and possible else
                self.scopes.add((getLine(sibling), getScopeEnd(sibling)))
                if sibling.tag != 'exceptElse':
                    self.edges[getLine(child)].add(getLine(sibling))
                else:
                    self.edges[getLine(child)].add(getLine(sibling.getchildren()[0]))

                if handleElse:
                    self.edges[getLine(child)].add(getLine(elseblock[0]))

        oldEdges = clone(self.edges)
        for child in tryblock: # all nodes in the the try body
            self.handleNode(child)

        oldLast = clone(self.last)
        self.last = set()
        for child in (_child for _child in node.getchildren() if _child.tag=="except"): # all exception blocks
            self.handleNode(child)
            self.last = set()
        self.last = oldLast
        del oldLast

        for k in self.edges:
            if oldEdges[k] - self.edges[k]:
                for sibling in itertools.dropwhile("except".__ne__, node.getchildren()): # all the exceptions and possible else
                    if sibling.tag != 'else':
                        self.edges[k].add(getLine(sibling))
                    else:
                        self.edges[k].add(getLine(sibling.getchildren()[0]))
        del oldEdges

        for child in [n for n in node.getchildren() if n.tag=='except']:  # all the except tags
            self.handleNode(child)

        node.append(elseblock[0].getchildren()[0])
        self.getLastTryExceptLines(node)
        self.scopes.add((getLine(node), getScopeEnd(list(itertools.takewhile("except".__ne__, tryblock))[-1])))

        self.last.add(getLine(finallyBlock[0]))
        for fb in finallyBlock:
            for child in fb.getchildren():
                self.handleNode(child)
        self.connectTryFinally(tryblock[-1], finallyBlock[0].getchildren()[0])
        for child in [n for n in node.getchildren() if n.tag=='except']:
            self.connectTryFinally(child, finallyBlock[0].getchildren()[0])
        self.getLastTryFinallyLines(node)


    def handleTryExcept(self, node):
        #		print 'handling tryexcept on line', getLine(node) ##
        elseblock = node.getchildren()[-1]
        handleElse = False
        if elseblock.tag == 'else':
            handleElse = True
            self.scopes.add((getLine(elseblock)-1, getScopeEnd(elseblock)))
            node.remove(elseblock)

        tryblock = list(itertools.takewhile(lambda n: not n.tag.endswith("Error"), node.getchildren())) # all nodes in the the try body
        for child in tryblock:
            self.handleNode(child)
            for sibling in itertools.dropwhile(lambda n: not n.tag.endswith("Error"), node.getchildren()): # all the exceptions and possible else
                self.scopes.add((getLine(sibling), getScopeEnd(sibling)))
                if sibling.tag != 'else':
                    self.edges[getLine(child)].add(getLine(sibling))
                else:
                    self.edges[getLine(child)].add(getLine(sibling.getchildren()[0]))
            if handleElse:
                self.edges[getLine(child)].add(getLine(elseblock.getchildren()[0]))
        oldEdges = clone(self.edges)
        for child in itertools.takewhile("except".__ne__, node.getchildren()): # all nodes in the the try body
            self.handleNode(child)

        oldLast = clone(self.last)
        self.last = set()
        for child in (_child for _child in node.getchildren() if _child.tag=="except"): # all exception blocks
            self.handleNode(child)
            self.last = set()
        self.last = oldLast
        del oldLast
        for k in self.edges:
            if oldEdges[k] - self.edges[k]:
                for sibling in itertools.dropwhile("except".__ne__, node.getchildren()): # all the exceptions and possible else
                    if sibling.tag != 'else':
                        self.edges[k].add(getLine(sibling))
                    else:
                        self.edges[k].add(getLine(sibling.getchildren()[0]))
        del oldEdges

        node.append(elseblock)
        self.getLastTryExceptLines(node)
        self.scopes.add((getLine(node), getScopeEnd(list(itertools.takewhile(lambda n: not n.tag.endswith("Error"), tryblock))[-1])))


    def handleExcept(self, node):
        for child in node.getchildren():
            self.handleNode(child)


    def connectTryFinally(self, node, terminal):
        """ Connect the appropriate child nodes in `node` to the terminal """

        if len(node.getchildren()) != 0:
            if node.tag not in 'if tryexcept tryfinally'.split():
                for child in (c for c in node.getchildren() if c.tag.endswith("Error") or c.tag=='else'):
                    self.connectTryFinally(child.getchildren()[-1], terminal)
            else:
                elseblock = node.getchildren()[-1]
                handleElse = False
                if elseblock.tag == 'else' and elseblock.text != '-':
                    handleElse = True
                    node.remove(elseblock)

                if not handleElse:
                    last = list(itertools.takewhile(lambda n: not n.tag.endswith("Error"), node.getchildren()))[-1] # all nodes in the the try body
                    self.connectTryFinally(last, terminal)

                    for child in itertools.dropwhile(lambda n: not n.tag.endswith("Error"), node.getchildren()): # all exceptions
                        self.connectTryFinally(child.getchildren()[-1], terminal)
                else:
                    #					connectTryFinally(elseblock.getchildren()[-1], terminal)
                    node.append(elseblock)

        else:
            self.edges[getLine(node)].add(getLine(terminal))


    def getLastTryExceptLines(self, node):

        if len(node.getchildren()) == 0 or all(n.tag in self.BLACKLIST for n in node.getchildren()):
            self.last.add(getLine(node))
        else:
            last = list(itertools.takewhile(lambda n: not n.tag.endswith("Error"), node.getchildren()))[-1]
            for i in range(getLine(node), getLine(last)+1):
                if i in self.last:
                    self.last.remove(i)

            handleElse = False
            if node.getchildren()[-1].tag == 'else' and node.getchildren()[-1].text != '-':
                handleElse = True

            for child in itertools.dropwhile(lambda n: not n.tag.endswith("Error"), node.getchildren()):
                self.getLastTryExceptLines(child.getchildren()[-1])


    def getLastTryFinallyLines(self, node):
        #		print getLine(node) ##
        if len(node.getchildren()) == 0 or all(n.tag in self.BLACKLIST for n in node.getchildren()):
            #			print 'adding last TF line', getLine(node) ##
            self.last.add(getLine(node))
        else:
            last = node.getchildren()[-1]
            for i in range(getLine(node), getLine(last)+1):
                if i in self.last:
                    self.last.remove(i)

            if last.tag in 'if tryfinally tryexcept'.split():
                if last.tag == 'if':
                    elseblock = last.getchildren()[-1]
                    last.remove(elseblock)
                    if elseblock.text != '-':
                        self.getLastTryFinallyLines(elseblock)
                    self.getLastTryFinallyLines(last.getchildren()[-1])

                elif last.tag == 'tryfinally':
                    self.getLastTryFinallyLines(last)

                else: # last.tag == 'tryexcept'
                    self.getLastTryExceptLines(last)
            else:
                self.getLastTryFinallyLines(last)


    def handleExpr(self, node):
        for child in node.getchildren():
            self.handleNode(child)


    def handleReturn(self, node):
        for child in node.getchildren():
            self.handleNode(child)
        src = getLastLine(child)

        parent = node.getparent()
        while parent.tag != 'functiondef':
            parent = parent.getparent()

        self.edges[src].add(getLine(parent))
        if src in self.last:
            self.last.remove(src)


    def handleAtomic(self, node): return


    def handleCall(self, node):
        #		handle = False
        callTo = getLastLine(node.getchildren()[0])
        self.edges[getLine(node)].add(callTo)

        #		for child in node.getchildren():
        #			handle = True
        #			self.handleNode(child)

        self.last = set(getCallLast(node)).union([getLastLine(node)])
        self.last.add(float("%d.%d" %(callTo, getLine(node))))

        #		if handle:
        #		first = getLine(node.getchildren()[0])
        #		last = getScopeEnd(node.getchildren()[-1])
        #		self.scopes.add((first, last))

        if getLine(node) in self.last:
            self.last.remove(getLine(node))

    HANDLERS = {
                'augassign': handleAugAssign,
                'binop': handleBinOp,
                'break': handleBreak,
                'call': handleCall,
                'compare': handleCompare,
                # 'else': handleElse,
                'exception': handleExcept,
                'expr': handleExpr,
                'for': handleLoop,
                'functiondef': handleFunctionDef,
                'if': handleIf,
                'import': handleImport,
                'importfrom': handleImportFrom,
                'module': handleModule,
                'print': handlePrint,
                'return': handleReturn,
                'try': handleTry,
                'except': handleTryExcept,
                'while' : handleLoop,
                'constant' : handleAtomic,
                'add' : handleAtomic,
                'name' : handleAtomic,
                'gt' : handleAtomic,
            }


def getModuleScope(node, answer=None):

    if answer is None: answer = 0
    try:
        answer = max(answer, getLine(node))
    except ValueError:
        pass
    if not len(node.getchildren()):
        return answer
    else:
        for child in node.getchildren():
            answer = max(getModuleScope(child, answer), answer)
        return answer


def getScopeEnd(node):
    if node.tag == 'call' or not len(node.getchildren()):
        return getLine(node)
    else:
        i = -1
        last = node.getchildren()[i]
        while last.text == '-':
            i -= 1
            last = node.getchildren()[i]

        return getScopeEnd(last)


def getLine(node):
    return int(node.text.strip().partition('\n')[0])


def getLastLine(node):
    #	print getLine(node) ##
    if all(child.tag in CFG.BLACKLIST for child in node.getchildren()):
        return getLine(node)
    else:
        answer = 0
        for child in (child for child in node.getchildren() if child.tag not in CFG.BLACKLIST and child.tag != 'call'):
            answer = max(getLastLine(child), answer, getLine(node))
        return answer

#def getLastLine(node):
##	print getLine(node) ##
#	if all(child.tag in CFG.BLACKLIST for child in node.getchildren()):
#		return getLine(node)
#	else:
#		answer = None
#		for child in (child for child in node.getchildren() if child.tag not in CFG.BLACKLIST and child.tag != 'call'):
#			answer = max(getLastLine(child), answer, getLine(node))
#		if not len([child for child in node.getchildren() if child.tag not in CFG.BLACKLIST and child.tag != 'call']):
#			answer = max(getLastLine(child), answer, getLine(node.getchildren()[-1]))
#		return answer


def getCallLast(node):
    if node.tag not in CFG.BLACKLIST and (node.tag == 'return' or not len(node.getchildren())):
        return [getLine(node)]
    return flattenList([getCallLast(child) for child in node.getchildren() if child.tag != "call" or any(i in child.tag for i in "if else try except finally".split())])


def getTop(node):
    if node.tag != 'tryfinally':
        return node
    else:
        return node.getchildren()[0].getchildren()[0].getchildren[0]


if __name__ == "__main__":
    print('starting')

    expected = defaultdict(set)
    #	expected[0] = set([32])
    #	expected[32] = set([33])
    #	expected[33] = set([34])
    #	expected[34] = set([35, 42])
    #	expected[35] = set([36])
    #	expected[36] = set([37, 40])
    #	expected[37] = set([38])
    #	expected[38] = set([43])
    #	expected[40] = set([34])
    #	expected[42] = set([43])
    #	expected[43] = set([])
    expected[0] = set([16])
    expected[16] = set([20])
    expected[20] = set([21])
    expected[21] = set([22])
    expected[22] = set([23, 26])
    expected[23] = set([24])
    expected[24] = set([28])
    expected[26] = set([28])
    expected[28] = set([29])
    expected[29] = set([])

    xml = 'output.xml'
    cfg = CFG(xml)
    cfg.parse()
    #	for k in sorted(cfg.edges): print k, sorted(cfg.edges[k]), '\t', cfg.edges[k] == expected[k], '\t', sorted(expected[k]) if cfg.edges[k] != expected[k] else ""
    for k in sorted(cfg.edges): print(k, ":", sorted(cfg.edges[k]), ',')
    print(sorted(cfg.scopes))
    print('done')