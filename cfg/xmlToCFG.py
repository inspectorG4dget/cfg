import lxml.etree as ET

from itertools import ifilter
from collections import defaultdict
from compiler.ast import Node
from platform import node

class CFG:
	BLACKLIST = set([
					'add',
					'divide',
					'eq',
					'mod',
					'multiply',
					'name',
					'num',
					'pow',
					'str',
					'subtract',
					])
	
	CONTAINERS = set([
					'else',
					])
	
	LOOPBACKS = set([
					'for',
					'while',
					])
	
	LOOPBACKNODES = set()
	
	def __init__(self, xmlFilePath):
		self.xml = ET.parse(xmlFilePath).getroot()
		self.nodes = set()
		self.edges = defaultdict(set)
		self.last = set()
	
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
			if node.tag in self.LOOPBACKNODES:
				self.LOOPBACKNODES.add(curr)
			if curr not in self.last:
				delete = set()
				for last in self.last:
					if curr > last or last in self.LOOPBACKNODES:
#						if curr == 13: print 'hoo', self.last
						self.edges[last].add(curr)
						delete.add(last)
				self.last -= delete
				if node.tag not in self.CONTAINERS:
					self.last.add(curr)
		
		if node.tag not in self.BLACKLIST and node.tag not in self.CONTAINERS:
			self.HANDLERS[node.tag](self, node)
		for child in (c for c in node.getchildren() if c.tag not in self.BLACKLIST and c.tag not in self.CONTAINERS):
			self.handleNode(child)
			delete = set()
			for last in self.last:
				if curr > last or last in self.LOOPBACKNODES:
					self.edges[last].add(curr)
					delete.add(last)
#			if node.tag not in self.BLACKLIST:
#				self.last.add(curr)
			self.last -= delete
			
		if node.tag in self.LOOPBACKS:
			for i in range(getLine(node)+1, getLine(getLastChild(node))+1):
				if i in self.last:
					self.last.remove(i)
			
		return 1
		
	def handleIf(self, node):
		compares = (c for c in node.getchildren() if c.tag == "compare")
		for compare in compares:
			self.handleNode(compare)
		self.last.update(set(getLine(c) for c in node.getchildren() if c.tag == "compare"))
		for child in (c for c in node.getchildren() if c.tag in ["else"]): # if body
			for grandChild in child.getchildren():
				self.handleNode(grandChild)
				if grandChild.getnext() not in ['else', 'elif']:
					self.last.update(set(getLine(c) for c in node.getchildren() if c.tag == "compare"))
		
		return 1
	
	def handleCompare(self, node):
		for child in node.getchildren():
			self.handleNode(child)
#		self.last.remove(getLine(node))
	
		return 1
	
	def handleElse(self, node):
		for child in node.getchildren():
			self.handleNode(child)
	
		return 1

	def handleLoop(self, node):
		start = getLine(node)
		
		if node.tag == 'for':
			dels = []
			for i,child in enumerate(node.getchildren()):
				if child.tag == 'else' and child.text == '-': # this should really only be the last child, but still ...
					dels.append(i)
			for d in dels[::-1]:
				node.remove(node.getchildren()[d])
		
		for child in node.getchildren():
			self.handleNode(child)
		end = getLine(getLastChild(node))
		self.edges[end].add(start)
		self.edges[start].add(getLine(node.getnext()))
		
		self.last.remove(end)
		
		return 1
	
	def handleFunctionDef(self, node):
		return 1
	
	def handleExpr(self, node):
		return 1
	
	def handlePrint(self, node):
		for child in node.getchildren():
			if not self.handleNode(child):
				self.removeNode(getLine(node))
		return 1
	
	def handleBinOp(self, node):
		return 1
	
	def handleReturn(self, node):
		return 1
	
	def handleModule(self, node):
		return 1
	
	def handleBinOp(self, node):
		return 1
	
	def handleAugAssign(self, node):
		return 1
	
	def handleBreak(self, node):
		next = node
		while next.tag not in self.LOOPBACKS:
			next = next.getparent()
		next = next.getnext()
		self.edges[getLine(node)].add(getLine(next))
		self.last.remove(getLine(node))
	
	HANDLERS = {'if': handleIf,
				'compare': handleCompare,
				'else': handleElse,
				'functiondef': handleFunctionDef,
				'expr': handleExpr,
				'module': handleModule,
				'print': handlePrint,
				'binop': handleBinOp,
				'return': handleReturn,
				'for': handleLoop,
				'augassign': handleAugAssign,
				'break': handleBreak,
				}

def getLine(node):
	return int(node.text.strip().partition('\n')[0])

def getLastChild(node, answer=None):
	""" The default `answer` argument is not depricated.
		It's used when there are no children."""
	answer = node
	for child in node.getchildren():
		answer = child
		answer = getLastChild(answer)
	return answer

if __name__ == "__main__":
	print 'starting'
	xfilepath = 'output.xml'
	cfg = CFG(xfilepath)
	cfg.handleNode(cfg.xml)
	
	expected = defaultdict(set)
	expected[0] = set([32])
	expected[32] = set([33])
	expected[33] = set([34])
	expected[34] = set([35, 41])
	expected[35] = set([36])
	expected[36] = set([37, 40])
	expected[37] = set([38])
	expected[38] = set([41])
	expected[40] = set([34])
	expected[41] = set([])
	
	for k in sorted(cfg.nodes):
		print k, sorted(cfg.edges[k]), '\t', cfg.edges[k] == expected[k], sorted(expected[k]) if cfg.edges[k] != expected[k] else ""
	
	print 'done'