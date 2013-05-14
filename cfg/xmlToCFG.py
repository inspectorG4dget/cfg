import lxml.etree as ET
from collections import defaultdict
from Tkconstants import LAST

class CFG:
	
	BLACKLIST = set(""" 
						add
						eq
						geq
						gte
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
			node.append(elseblock)
	
	def handleLoop(self, node):
		elseblock = node.getchildren()[-1]
		node.remove(elseblock)
		handleElse = False
		if elseblock.text != '-':
			handleElse = True
		for child in node.getchildren():
			self.handleNode(child)
		
		if handleElse:
			if node.getnext() is not None:
				self.edges[getLine(node)].add(getLine(elseblock.getchildren()[0]))	
			for child in elseblock.getchildren():
				self.handleNode(child)
		
	
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
	
	HANDLERS = {
				'augassign': handleAugAssign,
				'binop': handleBinOp,
				'break': handleBreak,
				'compare': handleCompare,
#				'else': handleElse,
#				'expr': handleExpr,
				'for': handleLoop,
				'functiondef': handleFunctionDef,
				'if': handleIf,
				'module': handleModule,
				'print': handlePrint,
#				'return': handleReturn,
				}


def getLine(node):
	return int(node.text.strip().partition('\n')[0])

def getTop(node):
	if node.tag != 'tryfinally':
		return node
	else:
		return node.getchildren()[0].getchildren()[0].getchildren[0]
	
if __name__ == "__main__":
	print 'starting'
	
	expected = defaultdict(set)
	expected[0] = set([32])
	expected[32] = set([33])
	expected[33] = set([34])
	expected[34] = set([35, 42])
	expected[35] = set([36])
	expected[36] = set([37, 40])
	expected[37] = set([38])
	expected[38] = set([43])
	expected[40] = set([34])
	expected[42] = set([43])
	expected[43] = set([])
	
	xml = 'output.xml'
	cfg = CFG(xml)
	cfg.parse()
	for k in sorted(cfg.edges): print k, sorted(cfg.edges[k]), '\t', cfg.edges[k] == expected[k], '\t', sorted(expected[k]) if cfg.edges[k] != expected[k] else ""
	
	print 'done'