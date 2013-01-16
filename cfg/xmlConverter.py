import _ast
from xml.dom.minidom import Document

class xmlConverter(object):

    FUNCTIONS = {}
    
    def __init__(self, codefilepath, doc=None):
        if not doc:
        	doc = Document()
        self.doc = doc
        self.root = self.getRoot(codefilepath)
    
    def generateXML(self):
    	self.handleNode(self.doc, self.doc, self.root)
    
    def getName(self, astnode):
        if hasattr(astnode, '_cfg_type'):
            return astnode._cfg_type
        
        if isinstance(astnode, _ast.ExceptHandler):
            if not astnode.type:
            	return "except"
            else:
            	return astnode.type.id
            	
        name = astnode.__class__.__name__.lower()
        astnode._cfg_type = name
        return name
    
    def getRoot(self, filepath):
        return compile(open(filename).read(), filename, 'exec', _ast.PyCF_ONLY_AST)
    
    def handleNode(self, doc, parent, astnode):
        childName = self.getName(astnode)
        child = doc.createElement(childName)
        if not isinstance(astnode, _ast.Module):
            try:
                label = str(astnode.lineno)
            except:
                label = childName
            child.appendChild(self.doc.createTextNode(label))
        parent.appendChild(child)
        
        if not self.HANDLERS[astnode.__class__](self, doc, child, astnode):
            parent.childNodes.pop(-1)
        
        return 1
       
    def handleAtomic(self, doc, parent, astnode):
        childName = self.getName(astnode)
        child = doc.createElement(childName)
        try:
            label = str(astnode.lineno)
        except:
            label = childName
        child.appendChild(self.doc.createTextNode(label))
        parent.appendChild(child)
        
        return 1
       
    def handleAssert(self, doc, parent, astnode):
        childname = self.getName(astnode)
        child = doc.createElement(childname)
        child.appendChild(self.doc.createTextNode(str(astnode.lineno)))
        parent.appendChild(child)
        return 1
    
    def handleAttribute(self, doc, parent, astnode):
        pass
    
    def handleAugAssign(self, doc, parent, astnode):
        pass
    
    def handleAugLoad(self, doc, parent, astnode):
        pass
    
    def handleAugStore(self, doc, parent, astnode):
        pass
    
    def handleBinOp(self, doc, parent, astnode):
        pass
    
    def handleBitAnd(self, doc, parent, astnode):
        pass
    
    def handleBitOr(self, doc, parent, astnode):
        pass
    
    def handleBitXor(self, doc, parent, astnode):
        pass
    
    def handleBoolOp(self, doc, parent, astnode):
        pass
    
    def handleCall(self, doc, parent, astnode):
        childName = self.getName(astnode)
        child = doc.createElement(childName)
        child.appendChild(self.doc.createTextNode(str(astnode.lineno)))
        parent.appendChild(child)
        
        for node in self.FUNCTIONS[astnode.func.id].body:
            if not self.HANDLERS[node.__class__](self, doc, child, node):
                child.childNodes.pop(-1)
        
        return 1
    
    def handleClassDef(self, doc, parent, astnode):
        pass
    
    def handleContinue(self, doc, parent, astnode):
        pass
    
    def handleDel(self, doc, parent, astnode):
        pass
    
    def handleDelete(self, doc, parent, astnode):
        pass
    
    def handleDict(self, doc, parent, astnode):
        pass
    
    def handleDictComp(self, doc, parent, astnode):
        pass
    
    def handleEllipsis(self, doc, parent, astnode):
        pass
    
    def handleExceptHandler(self, doc, parent, astnode):
        childName = self.getName(astnode)
        child = doc.createElement(childName)
        
        child.appendChild(self.doc.createTextNode(str(astnode.lineno)))
        parent.appendChild(child)
        
        for node in astnode.body:
            if not self.HANDLERS[node.__class__](self, doc, child, node):
                child.childNodes.pop(-1)
    
    def handleExec(self, doc, parent, astnode):
        pass
    
    def handleExpr(self, doc, parent, astnode):
        childName = self.getName(astnode)
        child = doc.createElement(childName)
        child.appendChild(self.doc.createTextNode(str(astnode.lineno)))
        parent.appendChild(child)
        
        if not isinstance(astnode.value, _ast.Call):
            self.handleAtomic(self.doc, child, astnode.value)
        else:
            self.handleCall(self.doc, child, astnode.value)
        
        return 1
       
    def handleExtSlice(self, doc, parent, astnode):
        pass
    
    def handleLoop(self, doc, parent, astnode):
        childName = self.getName(astnode)
        child = doc.createElement(childName)
        
        child.appendChild(self.doc.createTextNode(str(astnode.lineno)))
        parent.appendChild(child)
        
        for node in astnode.body:
            if not self.HANDLERS[node.__class__](self, doc, child, node):
                child.childNodes.pop(-1)
        
        grandchildName = "else"
        grandchild = doc.createElement(grandchildName)
        grandchild.appendChild(self.doc.createTextNode(max('-', str(min((node.lineno for node in astnode.orelse if hasattr(node, 'lineno')))-1) )))
        child.appendChild(grandchild)
        for node in astnode.orelse:
            if not self.HANDLERS[node.__class__](self, doc, grandchild, node):
                child.childNodes.pop(-1)
        
        return 1
    
    def handleFunctionDef(self, doc, parent, astnode):
        self.FUNCTIONS[astnode.name] = astnode
        childName = self.getName(astnode)
        child = doc.createElement(childName)
        
        child.appendChild(self.doc.createTextNode(str(astnode.lineno)))
        parent.appendChild(child)
        
        for node in astnode.body:
            if not self.HANDLERS[node.__class__](self, doc, child, node):
                child.childNodes.pop(-1)
        
        return 1
    
    def handleGeneratorExp(self, doc, parent, astnode):
        pass
    
    def handleGlobal(self, doc, parent, astnode):
        pass
    
    def handleGtE(self, doc, parent, astnode):
        pass
    
    def handleIf(self, doc, parent, astnode):
        childName = self.getName(astnode)
        child = doc.createElement(childName)
        
        child.appendChild(self.doc.createTextNode(str(astnode.lineno)))
        parent.appendChild(child)
        
        for node in astnode.body:
            if not self.HANDLERS[node.__class__](self, doc, child, node):
                child.childNodes.pop(-1)
        
        grandchildName = "else"
        grandchild = doc.createElement(grandchildName)
        grandchild.appendChild(self.doc.createTextNode(max('-', str(min((node.lineno for node in astnode.orelse if hasattr(node, 'lineno')))-1) )))
        child.appendChild(grandchild)
        for node in astnode.orelse:
            if not self.HANDLERS[node.__class__](self, doc, grandchild, node):
                grandchild.childNodes.pop(-1)
        
        return 1
    
    def handleImportFrom(self, doc, parent, astnode):
        pass
    
    def handleIndex(self, doc, parent, astnode):
        pass
    
    def handleInteractive(self, doc, parent, astnode):
        pass
    
    def handleInvert(self, doc, parent, astnode):
        pass
    
    def handleIsNot(self, doc, parent, astnode):
        pass
    
    def handleLShift(self, doc, parent, astnode):
        pass
    
    def handleLambda(self, doc, parent, astnode):
        pass
    
    def handleList(self, doc, parent, astnode):
        pass
    
    def handleListComp(self, doc, parent, astnode):
        pass
    
    def handleLoad(self, doc, parent, astnode):
        pass
    
    def handleLtE(self, doc, parent, astnode):
        pass
    
    def handleModule(self, doc, parent, astnode):
        child = parent
        child.appendChild(self.doc.createTextNode(str(0)))
        
        for node in astnode.body:
            if not self.HANDLERS[node.__class__](self, doc, child, node):
                child.childNodes.pop(-1)
        
        return 1
    
    def handleName(self, doc, parent, astnode):
        pass
    
    def handleNotEq(self, doc, parent, astnode):
        pass
    
    def handleNotIn(self, doc, parent, astnode):
        pass
    
    def handleNum(self, doc, parent, astnode):
        pass
    
    def handleParam(self, doc, parent, astnode):
        pass
    
    def handlePyCF_ONLY_AST(self, doc, parent, astnode):
        pass
    
    def handleRShift(self, doc, parent, astnode):
        pass
    
    def handleRepr(self, doc, parent, astnode):
        pass
    
    def handleSet(self, doc, parent, astnode):
        pass
    
    def handleSetComp(self, doc, parent, astnode):
        pass
    
    def handleSlice(self, doc, parent, astnode):
        pass
    
    def handleSub(self, doc, parent, astnode):
        pass
    
    def handleSubscript(self, doc, parent, astnode):
        pass
    
    def handleSuite(self, doc, parent, astnode):
        pass
    
    def handleTryExcept(self, doc, parent, astnode):
        childName = self.getName(astnode)
        child = doc.createElement(childName)
        child.appendChild(self.doc.createTextNode(str(astnode.lineno)))
        parent.appendChild(child)
        
        for node in astnode.body:
            if not self.HANDLERS[node.__class__](self, doc, child, node):
                child.childNodes.pop(-1)
        
        for node in astnode.handlers:
            childName = self.getName(node)
            child = doc.createElement(childName)
            child.appendChild(self.doc.createTextNode(str(astnode.lineno)))
            parent.appendChild(child)
            
            if not self.HANDLERS[node.__class__](self, doc, child, node):
                child.childNodes.pop(-1)
        
        for node in astnode.orelse:
            childName = "else"
            child = doc.createElement(childName)
            child.appendChild(self.doc.createTextNode(str(astnode.lineno)))
            parent.appendChild(child)
            
            if not self.HANDLERS[node.__class__](self, doc, child, node):
                child.childNodes.pop(-1)
        
        return 1
    
    def handleTryFinally(self, doc, parent, astnode):
        childName = self.getName(astnode)
        child = doc.createElement(childName)
        child.appendChild(self.doc.createTextNode(str(astnode.lineno)))
        parent.appendChild(child)
        
        for node in astnode.body:
            if not self.HANDLERS[node.__class__](self, doc, child, node):
                child.childNodes.pop(-1)
        
        childName = "finally"
        child = doc.createElement(childName)
        child.appendChild(self.doc.createTextNode(str(astnode.lineno)))
        parent.appendChild(child)
        for node in astnode.finalbody:
            if not self.HANDLERS[node.__class__](self, doc, child, node):
                child.childNodes.pop(-1)
        
        return 1
    
    def handleTuple(self, doc, parent, astnode):
        pass
    
    def handleUAdd(self, doc, parent, astnode):
        pass
    
    def handleUSub(self, doc, parent, astnode):
        pass
    
    def handleUnaryOp(self, doc, parent, astnode):
        pass
    
    def handleWhile(self, doc, parent, astnode):
        pass
    
    def handleWith(self, doc, parent, astnode):
        pass
    
    def handle__doc__(self, doc, parent, astnode):
        pass
    
    def handle__name__(self, doc, parent, astnode):
        pass
    
    def handle__package__(self, doc, parent, astnode):
        pass
    
    def handle__version__(self, doc, parent, astnode):
        pass
    
    def handlealias(self, doc, parent, astnode):
        pass
    
    def handlearguments(self, doc, parent, astnode):
        pass
    
    def handleboolop(self, doc, parent, astnode):
        pass
    
    def handlecmpop(self, doc, parent, astnode):
        pass
    
    def handlecomprehension(self, doc, parent, astnode):
        pass
    
    def handleexcepthandler(self, doc, parent, astnode):
        pass
    
    def handleexpr(self, doc, parent, astnode):
        pass
    
    def handleexpr_context(self, doc, parent, astnode):
        pass
    
    def handlekeyword(self, doc, parent, astnode):
        pass
    
    def handlemod(self, doc, parent, astnode):
        pass
    
    def handleoperator(self, doc, parent, astnode):
        pass
    
    def handleslice(self, doc, parent, astnode):
        pass
    
    def handlestmt(self, doc, parent, astnode):
        pass
    
    def handleunaryop(self, doc, parent, astnode):
        pass
    
    HANDLERS = {
        _ast.Add			: handleAtomic,
        _ast.And			: handleAtomic,
        _ast.Assert			: handleAtomic,
        _ast.Assign			: handleAtomic,
        _ast.AugAssign		: handleAtomic,
        _ast.BinOp			: handleAtomic,
        _ast.BitAnd			: handleAtomic,
        _ast.BitOr			: handleAtomic,
        _ast.BitXor			: handleAtomic,
        _ast.BoolOp			: handleAtomic,
        _ast.Break			: handleAtomic,
        _ast.Call			: handleCall,
        _ast.ClassDef		: handleClassDef,
        _ast.Compare		: handleAtomic,
        _ast.Continue		: handleAtomic,
        _ast.Del			: handleAtomic,
        _ast.Delete			: handleDelete,
        _ast.Dict			: handleDict,
        _ast.DictComp		: handleDictComp,
        _ast.Div			: handleAtomic,
        _ast.Ellipsis		: handleEllipsis,
        _ast.Eq				: handleAtomic,
        _ast.ExceptHandler	: handleExceptHandler,
        _ast.Exec			: handleExec,
        _ast.Expr			: handleExpr,
        _ast.Expression		: handleAtomic,
        _ast.ExtSlice		: handleExtSlice,
        _ast.FloorDiv		: handleAtomic,
        _ast.For			: handleLoop,
        _ast.FunctionDef	: handleFunctionDef,
        _ast.GeneratorExp	: handleGeneratorExp,
        _ast.Global			: handleGlobal,
        _ast.Gt				: handleAtomic,
        _ast.GtE			: handleAtomic,
        _ast.If				: handleIf,
        _ast.IfExp			: handleAtomic,
        _ast.Import			: handleAtomic,
        _ast.ImportFrom		: handleImportFrom,
        _ast.In				: handleAtomic,
        _ast.Index			: handleIndex,
        _ast.Interactive	: handleInteractive,
        _ast.Invert			: handleInvert,
        _ast.Is				: handleAtomic,
        _ast.IsNot			: handleIsNot,
        _ast.LShift			: handleLShift,
        _ast.Lambda			: handleLambda,
        _ast.List			: handleList,
        _ast.ListComp		: handleListComp,
        _ast.Load			: handleLoad,
        _ast.Lt				: handleAtomic,
        _ast.LtE			: handleLtE,
        _ast.Mod			: handleAtomic,
        _ast.Module			: handleModule,
        _ast.Mult			: handleAtomic,
        _ast.Name			: handleName,
        _ast.Not			: handleAtomic,
        _ast.NotEq			: handleNotEq,
        _ast.NotIn			: handleNotIn,
        _ast.Num			: handleNum,
        _ast.Or				: handleAtomic,
        _ast.Param			: handleParam,
        _ast.Pass			: handleAtomic,
        _ast.Pow			: handleAtomic,
        _ast.Print			: handleAtomic,
        _ast.PyCF_ONLY_AST	: handlePyCF_ONLY_AST,
        _ast.RShift			: handleRShift,
        _ast.Raise			: handleAtomic,
        _ast.Repr			: handleRepr,
        _ast.Return			: handleAtomic,
        _ast.Set			: handleSet,
        _ast.SetComp		: handleSetComp,
        _ast.Slice			: handleSlice,
        _ast.Store			: handleAtomic,
        _ast.Str			: handleAtomic,
        _ast.Sub			: handleSub,
        _ast.Subscript		: handleSubscript,
        _ast.Suite			: handleSuite,
        _ast.TryExcept		: handleTryExcept,
        _ast.TryFinally		: handleTryFinally,
        _ast.Tuple			: handleTuple,
        _ast.UAdd			: handleUAdd,
        _ast.USub			: handleUSub,
        _ast.UnaryOp		: handleUnaryOp,
        _ast.While			: handleLoop,
        _ast.With			: handleWith,
        _ast.Yield			: handleAtomic,
        _ast.alias			: handlealias,
        _ast.arguments		: handlearguments,
        _ast.boolop			: handleboolop,
        _ast.cmpop			: handlecmpop,
        _ast.comprehension	: handlecomprehension,
        _ast.excepthandler	: handleexcepthandler,
        _ast.expr			: handleexpr,
        _ast.expr_context	: handleexpr_context,
        _ast.keyword		: handlekeyword,
        _ast.mod			: handlemod,
        _ast.operator		: handleoperator,
        _ast.slice			: handleslice,
        _ast.stmt			: handlestmt,
        _ast.unaryop		: handleunaryop
    }

if __name__ == "__main__":
    filename = 'test.py'
    print 'starting'
    
    d = Document()
    x = xmlConverter(d)
    x.generateXML()
    
    print x.doc.toprettyxml('    ')
    
    print 'done'