import lxml.etree as ET
import itertools

from collections import defaultdict
from copy import deepcopy as clone

class CFG:
	
	BLACKLIST = set(""" 
						add
						eq
						geq
						gt
						gte
						lt
						leq
						lte
						mod
						name
						num
						pow
						str
					""".split())
	
	LOOPS = set('for while'.split())
	
	def __init__(self, xmlFilePath):
		self.xml = ET.parse(xmlFilePath).getroot()
		self.nodes = set()
		self.edges = defaultdict(set)
		self.last = set([getLine(self.xml)])
		self.scopes = []
		self.currScope = []
		
	def parse(self):
		for child in self.xml.getchildren():
			self.handleNode(child)
	
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
			
			self.last.add(curr)
			if node.tag.endswith("Error"):
				self.HANDLERS['exception'](self, node)
			else:
				self.HANDLERS[node.tag](self, node)
	
	def handleIf(self, node):
		elseblock = node.getchildren()[-1]
		handleElse = False
		if elseblock.text != '-':
			self.edges[getLine(node)].add(getLine(elseblock.getchildren()[0]))
			node.remove(elseblock)
			handleElse = True
		
		for child in node.getchildren():
#			self.last.add(getLine(node))
			self.handleNode(child)
		
		for child in node.getchildren():
			try:
				self.last.remove(getLine(child))
			except KeyError:
				pass
		self.last.add(getLine(node))
		
		if handleElse:
			for child in elseblock.getchildren():
				self.handleNode(child)
			self.scopes.append((getLine(node), getLastLine(node)))
			self.scopes.append((getLine(elseblock), getLastLine(elseblock)))
			node.append(elseblock)
	
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
		del oldLast
		
		for child in node.getchildren():
			self.handleNode(child)
		
		if not handleElse:
			if node.getnext() is not None:
				self.edges[getLine(node)].add(getLine(node.getnext()))
		
		self.handleLoopback(node)
		self.scopes.append((getLine(node), getLastLine(node)))
		if handleElse:
			self.scopes.append((getLine(elseblock), getLastLine(elseblock)))
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
			if elseblock.text != '-':
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
		for child in node.getchildren():
			self.handleNode(child)
	
	def handleModule(self, node):
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
	
	def handleTryFinally(self, node):
		tryexcept, finallyBlock = node.getchildren()
		self.scopes.append((getLine(finallyBlock.getchildren()[0]), getLastLine(finallyBlock)))
		self.scopes.append((getLine(tryexcept), getLastLine(tryexcept)))
		
		self.handleNode(tryexcept)
		self.last.add(getLine(finallyBlock))
		for child in finallyBlock.getchildren():
			self.handleNode(child)
		self.connectTryFinally(tryexcept, finallyBlock.getchildren()[0])
		self.getLastTryFinallyLines(node)
	
	def handleTryExcept(self, node):
#		print 'handling tryexcept on line', getLine(node) ##
		elseblock = node.getchildren()[-1]
		handleElse = False
		if elseblock.tag == 'else':
			handleElse = True
			self.scopes.append((getLine(elseblock)-1, getLastLine(elseblock)))
			node.remove(elseblock)
		
		tryblock = list(itertools.takewhile(lambda n: not n.tag.endswith("Error"), node.getchildren())) # all nodes in the the try body
		for child in tryblock:
			self.handleNode(child)
			for sibling in itertools.dropwhile(lambda n: not n.tag.endswith("Error"), node.getchildren()): # all the exceptions and possible else
				self.scopes.append((getLine(sibling), getLastLine(sibling)))
				if sibling.tag != 'else':
					self.edges[getLine(child)].add(getLine(sibling))
				else:
					self.edges[getLine(child)].add(getLine(sibling.getchildren()[0]))
			if handleElse:
				self.edges[getLine(child)].add(getLine(elseblock.getchildren()[0]))	
		
		oldEdges = clone(self.edges)
		for child in itertools.takewhile(lambda n: not n.tag.endswith("Error"), node.getchildren()): # all nodes in the the try body
			self.handleNode(child)
		
		oldLast = clone(self.last)
		self.last = set()
		for child in (_child for _child in node.getchildren() if _child.tag.endswith("Error")): # all exception blocks
			self.handleNode(child)
			self.last = set()
		self.last = oldLast
		del oldLast
		
		for k in self.edges:
			if oldEdges[k] - self.edges[k]:
				for sibling in itertools.dropwhile(lambda n: not n.tag.endswith("Error"), node.getchildren()): # all the exceptions and possible else
					if sibling.tag != 'else':
						self.edges[k].add(getLine(sibling))
					else:
						self.edges[k].add(getLine(sibling.getchildren()[0]))
		del oldEdges
		
			
		node.append(elseblock)
		self.getLastTryExceptLines(node)
		self.scopes.append((getLine(node), getLastLine(list(itertools.takewhile(lambda n: not n.tag.endswith("Error"), tryblock))[-1])))
	
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
	
	def handleCall(self, node):
		for child in node.getchildren():
			self.handleNode(child)
			
	
	HANDLERS = {
				'augassign': handleAugAssign,
				'binop': handleBinOp,
				'break': handleBreak,
				'call': handleCall,
				'compare': handleCompare,
#				'else': handleElse,
				'exception': handleExcept,
				'expr': handleExpr,
				'for': handleLoop,
				'functiondef': handleFunctionDef,
				'if': handleIf,
				'module': handleModule,
				'print': handlePrint,
				'tryfinally': handleTryFinally,
				'tryexcept': handleTryExcept,
#				'return': handleReturn,
				}


def getLine(node):
	return int(node.text.strip().partition('\n')[0])

def getLastLine(node):
	print getLine(node) ##
	if all(child.tag in CFG.BLACKLIST for child in node.getchildren()):
		return getLine(node)
	else:
		answer = None
		for child in (child for child in node.getchildren() if child.tag not in CFG.BLACKLIST):
			answer = max(getLastLine(child), answer)
		return answer

def getTop(node):
	if node.tag != 'tryfinally':
		return node
	else:
		return node.getchildren()[0].getchildren()[0].getchildren[0]
	
if __name__ == "__main__":
	print 'starting'
	
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
	for k in sorted(cfg.edges): print k, sorted(cfg.edges[k]), '\t', cfg.edges[k] == expected[k], '\t', sorted(expected[k]) if cfg.edges[k] != expected[k] else ""
	print sorted(cfg.scopes)
	print 'done'