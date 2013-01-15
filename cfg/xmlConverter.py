import _ast
from xml.dom.minidom import Document

FUNCTIONS = {}

def getName(astnode):
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

def getRoot(filepath):
    return compile(open(filename).read(), filename, 'exec', _ast.PyCF_ONLY_AST)

def handleNode(doc, parent, astnode):
    childName = getName(astnode)
    child = doc.createElement(childName)
    if not isinstance(astnode, _ast.Module):
        try:
            label = str(astnode.lineno)
        except:
            label = childName
        child.appendChild(doc.createTextNode(label))
    parent.appendChild(child)
    
    if not handlers[astnode.__class__](doc, child, astnode):
        parent.childNodes.pop(-1)
    
    return 1
   
def handleAtomic(doc, parent, astnode):
    childName = getName(astnode)
    child = doc.createElement(childName)
    try:
        label = str(astnode.lineno)
    except:
        label = childName
    child.appendChild(doc.createTextNode(label))
    parent.appendChild(child)
    
    return 1
   
def handleAssert(doc, parent, astnode):
    childname = getName(astnode)
    child = doc.createElement(childname)
    child.appendChild(doc.createTextNode(str(astnode.lineno)))
    parent.appendChild(child)
    return 1

def handleAttribute(doc, parent, astnode):
    pass

def handleAugAssign(doc, parent, astnode):
    pass

def handleAugLoad(doc, parent, astnode):
    pass

def handleAugStore(doc, parent, astnode):
    pass

def handleBinOp(doc, parent, astnode):
    pass

def handleBitAnd(doc, parent, astnode):
    pass

def handleBitOr(doc, parent, astnode):
    pass

def handleBitXor(doc, parent, astnode):
    pass

def handleBoolOp(doc, parent, astnode):
    pass

def handleCall(doc, parent, astnode):
    childName = getName(astnode)
    child = doc.createElement(childName)
    child.appendChild(doc.createTextNode(str(astnode.lineno)))
    parent.appendChild(child)
    
    for node in FUNCTIONS[astnode.func.id].body:
        if not handlers[node.__class__](doc, child, node):
            child.childNodes.pop(-1)
    
    return 1

def handleClassDef(doc, parent, astnode):
    pass

def handleContinue(doc, parent, astnode):
    pass

def handleDel(doc, parent, astnode):
    pass

def handleDelete(doc, parent, astnode):
    pass

def handleDict(doc, parent, astnode):
    pass

def handleDictComp(doc, parent, astnode):
    pass

def handleEllipsis(doc, parent, astnode):
    pass

def handleExceptHandler(doc, parent, astnode):
    childName = getName(astnode)
    child = doc.createElement(childName)
    
    child.appendChild(doc.createTextNode(str(astnode.lineno)))
    parent.appendChild(child)
    
    for node in astnode.body:
        if not handlers[node.__class__](doc, child, node):
            child.childNodes.pop(-1)

def handleExec(doc, parent, astnode):
    pass

def handleExpr(doc, parent, astnode):
    childName = getName(astnode)
    child = doc.createElement(childName)
    child.appendChild(doc.createTextNode(str(astnode.lineno)))
    parent.appendChild(child)
    
    if not isinstance(astnode.value, _ast.Call):
        handleAtomic(doc, child, astnode.value)
    else:
        handleCall(doc, child, astnode.value)
    
    return 1
   
def handleExtSlice(doc, parent, astnode):
    pass

def handleLoop(doc, parent, astnode):
    childName = getName(astnode)
    child = doc.createElement(childName)
    
    child.appendChild(doc.createTextNode(str(astnode.lineno)))
    parent.appendChild(child)
    
    for node in astnode.body:
        if not handlers[node.__class__](doc, child, node):
            child.childNodes.pop(-1)
    
    grandchildName = "else"
    grandchild = doc.createElement(grandchildName)
    grandchild.appendChild(doc.createTextNode(max('-', str(min((node.lineno for node in astnode.orelse if hasattr(node, 'lineno')))-1) )))
    child.appendChild(grandchild)
    for node in astnode.orelse:
        if not handlers[node.__class__](doc, grandchild, node):
            child.childNodes.pop(-1)
    
    return 1

def handleFunctionDef(doc, parent, astnode):
    FUNCTIONS[astnode.name] = astnode
    childName = getName(astnode)
    child = doc.createElement(childName)
    
    child.appendChild(doc.createTextNode(str(astnode.lineno)))
    parent.appendChild(child)
    
    for node in astnode.body:
        if not handlers[node.__class__](doc, child, node):
            child.childNodes.pop(-1)
    
    return 1

def handleGeneratorExp(doc, parent, astnode):
    pass

def handleGlobal(doc, parent, astnode):
    pass

def handleGtE(doc, parent, astnode):
    pass

def handleIf(doc, parent, astnode):
    childName = getName(astnode)
    child = doc.createElement(childName)
    
    child.appendChild(doc.createTextNode(str(astnode.lineno)))
    parent.appendChild(child)
    
    for node in astnode.body:
        if not handlers[node.__class__](doc, child, node):
            child.childNodes.pop(-1)
    
    grandchildName = "else"
    grandchild = doc.createElement(grandchildName)
    grandchild.appendChild(doc.createTextNode(max('-', str(min((node.lineno for node in astnode.orelse if hasattr(node, 'lineno')))-1) )))
    child.appendChild(grandchild)
    for node in astnode.orelse:
        if not handlers[node.__class__](doc, grandchild, node):
            grandchild.childNodes.pop(-1)
    
    return 1

def handleImportFrom(doc, parent, astnode):
    pass

def handleIndex(doc, parent, astnode):
    pass

def handleInteractive(doc, parent, astnode):
    pass

def handleInvert(doc, parent, astnode):
    pass

def handleIsNot(doc, parent, astnode):
    pass

def handleLShift(doc, parent, astnode):
    pass

def handleLambda(doc, parent, astnode):
    pass

def handleList(doc, parent, astnode):
    pass

def handleListComp(doc, parent, astnode):
    pass

def handleLoad(doc, parent, astnode):
    pass

def handleLtE(doc, parent, astnode):
    pass

def handleModule(doc, parent, astnode):
    child = parent
    child.appendChild(doc.createTextNode(str(0)))
    
    for node in astnode.body:
        if not handlers[node.__class__](doc, child, node):
            child.childNodes.pop(-1)
    
    return 1

def handleName(doc, parent, astnode):
    pass

def handleNotEq(doc, parent, astnode):
    pass

def handleNotIn(doc, parent, astnode):
    pass

def handleNum(doc, parent, astnode):
    pass

def handleParam(doc, parent, astnode):
    pass

def handlePyCF_ONLY_AST(doc, parent, astnode):
    pass

def handleRShift(doc, parent, astnode):
    pass

def handleRepr(doc, parent, astnode):
    pass

def handleSet(doc, parent, astnode):
    pass

def handleSetComp(doc, parent, astnode):
    pass

def handleSlice(doc, parent, astnode):
    pass

def handleSub(doc, parent, astnode):
    pass

def handleSubscript(doc, parent, astnode):
    pass

def handleSuite(doc, parent, astnode):
    pass

def handleTryExcept(doc, parent, astnode):
    childName = getName(astnode)
    child = doc.createElement(childName)
    child.appendChild(doc.createTextNode(str(astnode.lineno)))
    parent.appendChild(child)
    
    for node in astnode.body:
        if not handlers[node.__class__](doc, child, node):
            child.childNodes.pop(-1)
    
    for node in astnode.handlers:
        childName = getName(node)
        child = doc.createElement(childName)
    	child.appendChild(doc.createTextNode(str(astnode.lineno)))
        parent.appendChild(child)
        
        if not handlers[node.__class__](doc, child, node):
            child.childNodes.pop(-1)
    
    for node in astnode.orelse:
        childName = "else"
        child = doc.createElement(childName)
    	child.appendChild(doc.createTextNode(str(astnode.lineno)))
        parent.appendChild(child)
        
        if not handlers[node.__class__](doc, child, node):
            child.childNodes.pop(-1)
    
    return 1

def handleTryFinally(doc, parent, astnode):
    childName = getName(astnode)
    child = doc.createElement(childName)
    child.appendChild(doc.createTextNode(str(astnode.lineno)))
    parent.appendChild(child)
    
    for node in astnode.body:
        if not handlers[node.__class__](doc, child, node):
            child.childNodes.pop(-1)
    
    childName = "finally"
    child = doc.createElement(childName)
    child.appendChild(doc.createTextNode(str(astnode.lineno)))
    parent.appendChild(child)
    for node in astnode.finalbody:
    	if not handlers[node.__class__](doc, child, node):
            child.childNodes.pop(-1)
    
    return 1

def handleTuple(doc, parent, astnode):
    pass

def handleUAdd(doc, parent, astnode):
    pass

def handleUSub(doc, parent, astnode):
    pass

def handleUnaryOp(doc, parent, astnode):
    pass

def handleWhile(doc, parent, astnode):
    pass

def handleWith(doc, parent, astnode):
    pass

def handle__doc__(doc, parent, astnode):
    pass

def handle__name__(doc, parent, astnode):
    pass

def handle__package__(doc, parent, astnode):
    pass

def handle__version__(doc, parent, astnode):
    pass

def handlealias(doc, parent, astnode):
    pass

def handlearguments(doc, parent, astnode):
    pass

def handleboolop(doc, parent, astnode):
    pass

def handlecmpop(doc, parent, astnode):
    pass

def handlecomprehension(doc, parent, astnode):
    pass

def handleexcepthandler(doc, parent, astnode):
    pass

def handleexpr(doc, parent, astnode):
    pass

def handleexpr_context(doc, parent, astnode):
    pass

def handlekeyword(doc, parent, astnode):
    pass

def handlemod(doc, parent, astnode):
    pass

def handleoperator(doc, parent, astnode):
    pass

def handleslice(doc, parent, astnode):
    pass

def handlestmt(doc, parent, astnode):
    pass

def handleunaryop(doc, parent, astnode):
    pass
   
handlers = {
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
    root = getRoot(filename)
    handleNode(d, d, root)
    
    print d.toprettyxml('    ')
    
    print 'done'