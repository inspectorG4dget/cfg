import _ast
from xml.dom.minidom import Document
import collections
import sys
import os

class xmlConverter(object):

    FUNCTIONS = {}
    IMPORTS = collections.defaultdict(lambda : None) # also functions as the import stack to avoid expanding redundant imports
    MODULES = collections.defaultdict(set) # map module names to a set of their aliases
    callstack = [] # each item is an _ast object
    depth = 0
    
    def __init__(self, codefilepath, imported, modname=None, doc=None):
        if not doc:
            doc = Document()
        self.doc = doc
        self.root = self.getRoot(codefilepath)
        self.imported = imported
        self.modname = None
        if self.imported:
            if not modname:
                raise TypeError("An xmlConverter for an imported module MUST be supplied a module name")
            self.modname = modname
        if not self.modname:
        	self.modname = "module"
        self.funcname = None # used for handling aliasing the names of imported functions i.e. `from foo import bar as baz`
    
    def generateXML(self, funcname=None, asname=None):
        if funcname is None or funcname == "*":
            self.handleNode(self.doc, self.doc, self.root)
        else:
            if asname is not None:
                self.funcname = asname
            else:
                self.funcname = funcname
                
            for node in self.root.body:
                if isinstance(node, _ast.FunctionDef) and node.name == funcname:
                    self.handleNode(self.doc, self.doc, node)
                    
    
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
        return compile(open(filepath).read(), filepath, 'exec', _ast.PyCF_ONLY_AST)
    
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
        return 1
       
    def handleAssert(self, doc, root, astnode):
        
        if not self.handleNode(doc, root, astnode.test):
            root.childnodes.pop(-1)
                
        return 1
    
    def handleAttribute(self, doc, root, astnode):
        
        funcname = astnode.attr
        modname = astnode.value.id
        
        handle = True
        popcall = False
        if isinstance(astnode, _ast.Call): 
            if "%s.%s" %(modname, funcname) in self.callstack:
                handle = False
                if "%s.%s" %(modname, funcname) == self.callstack[-1]:
                    self.callstack.append("%s.%s" %(modname, funcname))
                    popcall = True
            else:
                self.callstack.append("%s.%s" %(modname, funcname))
                popcall = True
        
        if handle:
            for node in self.FUNCTIONS["%s.%s" %(modname, funcname)].body:
                if not self.handleNode(doc, root, self.FUNCTIONS["%s.%s" %(modname, funcname)]):
                    root.childNodes.pop(-1)
        else:
            root.appendChild(self.doc.createTextNode("loopback to %s" %funcname))
                
        if popcall:
            self.callstack.pop(-1)
                
    def handleAugAssign(self, doc, root, astnode):
        
        if not self.handleNode(doc, root, astnode.target):
            root.childNodes.pop(-1)
        
        if not self.handleNode(doc, root, astnode.op):
            root.childNodes.pop(-1)
            
        if not self.handleNode(doc, root, astnode.value):
            root.childNodes.pop(-1)
        
        return 1
    
    def handleAugLoad(self, doc, parent, astnode):
        pass
    
    def handleAugStore(self, doc, parent, astnode):
        pass
    
    def handleBinOp(self, doc, root, astnode):
        
        if not self.handleNode(doc, root, astnode.left):
            root.childNodes.pop(-1)
        
        if not self.handleNode(doc, root, astnode.op):
            root.childNodes.pop(-1)
        
        if not self.handleNode(doc, root, astnode.right):
            root.childNodes.pop(-1)
        
        return 1
    
    def handleBitAnd(self, doc, parent, astnode):
        return 1
    
    def handleBitOr(self, doc, parent, astnode):
        return 1
    
    def handleBitXor(self, doc, parent, astnode):
        return 1
    
    def handleBoolOp(self, doc, root, astnode):
        
        if not self.handleNode(doc, root, astnode.left):
            root.childNodes.pop(-1)
        if not self.handleNode(doc, root, astnode.op):
            root.childNodes.pop(-1)
        if not self.handleNode(doc, root, astnode.right):
            root.childNodes.pop(-1)
    
    def handleCall(self, doc, root, astnode):
        
        if isinstance(astnode.func, _ast.Attribute):	# this is an imported function
            self.handleAttribute(doc, root, astnode.func)
        else:
            for arg in astnode.args:
                if not self.handleNode(doc, root, arg):
                    root.childNodes.pop(-1)
            
            handle = True
            popcall = False
            if isinstance(astnode, _ast.Call): 
                if "%s.%s" %(self.modname if self.modname else "module", astnode.func.id) in self.callstack:
                    handle = False
                    if "%s.%s" %(self.modname if self.modname else "module", astnode.func.id) == self.callstack[-1]:
                        self.callstack.append("%s.%s" %(self.modname if self.modname else "module", astnode.func.id))
                        popcall = True
                else:
                    self.callstack.append("%s.%s" %(self.modname if self.modname else "module", astnode.func.id))
                    popcall = True
            
            if handle:
                for node in self.FUNCTIONS["%s.%s" %(self.modname, astnode.func.id)].body:
                    if not self.handleNode(doc, root, node):
                        root.childNodes.pop(-1)
            else:
                root.appendChild(self.doc.createTextNode("loopback to %s" %astnode.func.id))
                    
            if popcall:
                self.callstack.pop(-1)
        
        return 1
    
    def handleClassDef(self, doc, parent, astnode):
        pass
    
    def handleCompare(self, doc, root, astnode):
        
        self.handleNode(doc, root, astnode.left)
        
        for op in astnode.ops:
            if not self.handleNode(doc, root, op):
                root.childNodes.pop(-1)
       
        for comparator in astnode.comparators:
            if not self.handleNode(doc, root, comparator):
                root.childNodes.pop(-1)
        
        return 1
    
    def handleContinue(self, doc, parent, astnode):
        return 1
    
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
    
    def handleExceptHandler(self, doc, root, astnode):
        
        for node in astnode.body:
            if not self.handleNode(doc, root, node):
                root.childNodes.pop(-1)
        return 1
    
    def handleExec(self, doc, parent, astnode):
        pass
    
    def handleExpr(self, doc, root, astnode):
        if not self.handleNode(self.doc, root, astnode.value):
            root.childNodes.pop(-1)
        
        return 1
       
    def handleExtSlice(self, doc, parent, astnode):
        pass
    
    def handleLoop(self, doc, root, astnode):
        
        for node in astnode.body:
            if not self.handleNode(doc, root, node):
                root.childNodes.pop(-1)
        
        childName = "else"
        child = doc.createElement(childName)
        child.appendChild(self.doc.createTextNode(max('-', str(min((node.lineno for node in astnode.orelse if hasattr(node, 'lineno')))-1) )))
        root.appendChild(child)
        for node in astnode.orelse:
            if not self.handleNode(doc, child, node):
                child.childNodes.pop(-1)
        
        return 1
    
    def handleFunctionDef(self, doc, root, astnode):
        self.callstack.append("%s.%s" %(self.modname if self.modname else "module", astnode.name))
        self.FUNCTIONS["%s.%s" %(self.modname, self.funcname if self.funcname else astnode.name)] = astnode
        
        for node in astnode.args.args:
            if not self.handleNode(doc, root, node):
                root.childNodes.pop(-1)
        
        for node in astnode.body:
            if not self.handleNode(doc, root, node):
                root.childNodes.pop(-1)
        self.callstack.pop(-1)
        return 1
    
    def handleGeneratorExp(self, doc, parent, astnode):
        pass
    
    def handleGlobal(self, doc, parent, astnode):
        pass
    
    def handleGtE(self, doc, parent, astnode):
        pass
    
    def handleIf(self, doc, root, astnode):
        
        for node in astnode.body:
            if not self.handleNode(doc, root, node):
                root.childNodes.pop(-1)
        
        childName = "else"
        child = doc.createElement(childName)
        if astnode.orelse:
            child.appendChild(self.doc.createTextNode(max('-', str(min((node.lineno for node in astnode.orelse if hasattr(node, 'lineno')))-1) )))
            root.appendChild(child)
            for node in astnode.orelse:
                if not self.handleNode(doc, child, node):
                    child.childNodes.pop(-1)
        
        return 1
    
    def handleImport(self, doc, root, astnode): # TODO: Expand class and function defs inline
        for imported in astnode.names:
            if not imported.asname:
                imported.asname = imported.name
            modname, asname = imported.name, imported.asname
            
            if modname in self.MODULES: # module has been imported before (possibly under a different alias)
                if self.MODULES[modname] == asname: # module has been imported before under the same alias
                    root.appendChild(self.doc.createTextNode("Repeat import of %s as %s skipped" %(imported.name, imported.asname)))
                else: # module has been imported before under a different alias
                    if asname in self.IMPORTS: # module is being imported under a previously used alias
                        self.MODULES.remove(modname)
                        if not self.MODULES[modname]:
                            self.MODULES.pop(modname)
                        
                        self.IMPORTS[asname] = modname
                    
                    else:
                        self.IMPORTS[asname] = modname
                        self.MODULES[modname].add(asname)
                        addFuncs = {}
                        for funcname,func in self.FUNCTIONS.iteritems():
                            impmodname,_,funcname = funcname.partition('.') 
                            if modname == self.IMPORTS[impmodname]:
                                addFuncs["%s.%s" %(asname, funcname)] = self.FUNCTIONS["%s.%s" %(impmodname, funcname)]
                        self.FUNCTIONS.update(addFuncs)
                        root.appendChild(self.doc.createTextNode("Repeat import of %s as %s skipped" %(imported.name, imported.asname)))
            
            else:
                self.MODULES[modname].add(asname)
                if asname in self.IMPORTS:
                    self.MODULES[self.IMPORTS[asname]].remove(asname)
                    
                    # Remove all functions imported from this module as well
                    delkeys = []
                    for funcname in self.FUNCTIONS:
                        if funcname.partition('.')[0] == asname:
                            delkeys.append(funcname)
                    for k in delkeys:
                        self.FUNCTIONS.pop(k)
                    # Done Remove all functions imported from this module as well
                    
                    if not self.MODULES[self.IMPORTS[asname]]:
                        self.MODULES.pop(self.IMPORTS[asname])
                self.IMPORTS[asname] = modname
                
                for dirpath in sys.path:
                    fpath = os.path.join(dirpath, self.IMPORTS[imported.asname]) + '.py'
                    if os.path.exists(fpath):
                        root.appendChild(self.doc.createTextNode("import %s as %s" %(imported.name, imported.asname)))
                        x = xmlConverter(fpath, imported=True, modname=imported.asname)
                        x.generateXML()
                        break
        
        return 1
    
    def handleImportFrom(self, doc, root, astnode): # TODO: Expand class and function defs inline
        for name in astnode.names:
            if not name.asname:
            	name.asname = name.name
            if self.IMPORTS[name.asname] != "%s.%s" %(astnode.module, name.name):
                self.IMPORTS[name.asname] = "%s.%s" %(astnode.module, name.name)
                for dirname in sys.path:
                    fpath = os.path.join(dirname, astnode.module) +'.py'
                    if os.path.exists(fpath):
                        x = xmlConverter(fpath, imported=False, modname=astnode.module)
                        x.generateXML(name.name, name.asname)
                        break
                
                root.appendChild(doc.createTextNode("from %(modname)s import %(funcname)s as %(alias)s" 
                                                %{"modname":astnode.module, "funcname":name.name, "alias":name.asname}))
            else:
                root.appendChild(doc.createTextNode("Repeat import from %(modname)s of %(funcname)s as %(alias)s skipped" 
                                                %{"modname":astnode.module, "funcname":name.name, "alias":name.asname}))
                self.handleNode(self.doc, root, self.FUNCTIONS["module.%s" %name.asname])
        
        return 1
    
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
    
    def handleList(self, doc, root, astnode):
        
        for node in astnode.elts:
            if not self.handleNode(doc, root, node):
                root.childNodes.pop(-1)
        
        return 1
    
    def handleListComp(self, doc, parent, astnode):
        pass
    
    def handleLoad(self, doc, parent, astnode):
        pass
    
    def handleLtE(self, doc, parent, astnode):
        pass
    
    def handleModule(self, doc, root, astnode):
        
        root.appendChild(self.doc.createTextNode(str(0)))
        
        for node in astnode.body:
            # handle only functiondefs and classdefs in an imported module. Handle everything in the main (executed) module
            if not self.imported or any((isinstance(astnode, astype) for astype in [_ast.Module, _ast.FunctionDef, _ast.ClassDef])):
                if not self.handleNode(doc, root, node):
                    child.childNodes.pop(-1)
        
        return 1
    
    def handleName(self, doc, root, astnode):
        return 1
    
    def handleNotEq(self, doc, parent, astnode):
        pass
    
    def handleNotIn(self, doc, parent, astnode):
        pass
    
    def handleNum(self, doc, root, astnode):
        return 1
    
    def handleParam(self, doc, parent, astnode):
        pass
    
    def handlePrint(self, doc, root, astnode):
        
        for node in astnode.values:
            if not self.handleNode(doc, root, node):
                root.childNodes.pop(-1)
        return 1
    
    def handleRShift(self, doc, parent, astnode):
        pass
    
    def handleRepr(self, doc, root, astnode):
        
        if not self.handleNode(doc, root, astnode.value):
            root.childNodes.pop(-1)
        
        return 1
    
    def handleSet(self, doc, parent, astnode):
        pass
    
    def handleSetComp(self, doc, parent, astnode):
        pass
    
    def handleSlice(self, doc, root, astnode):
        if not self.handleNode(doc, root, astnode.lower):
            root.childNodes.pop(-1)
        if not self.handleNode(doc, root, astnode.step if astnode.step else _ast.Num(1)):
            root.childNodes.pop(-1)
        if not self.handleNode(doc, root, astnode.upper):
            root.childNodes.pop(-1)
        
        return 1
    
    def handleSub(self, doc, parent, astnode):
        pass
    
    def handleSubscript(self, doc, root, astnode):
        
        if not self.handleNode(doc, root, astnode.value):
            root.childNodes.pop(-1)
        if not self.handleNode(doc, root, astnode.slice):
            root.childNodes.pop(-1)
        
        return 1
    
    def handleSuite(self, doc, parent, astnode):
        pass
    
    def handleTryExcept(self, doc, root, astnode):
        
        for node in astnode.body:
            if not self.handleNode(doc, root, node):
                root.childNodes.pop(-1)
        
        for node in astnode.handlers:
            if not self.handleNode(doc, root, node):
                root.childNodes.pop(-1)
        
        for node in astnode.orelse:
            childName = "else"
            child = doc.createElement(childName)
            child.appendChild(self.doc.createTextNode(str(node.lineno)))
            root.appendChild(child)
            
            if not self.handleNode(doc, child, node):
                child.childNodes.pop(-1)
        
        return 1
    
    def handleTryFinally(self, doc, root, astnode):
        
        for node in astnode.body:
            if not self.handleNode(doc, root, node):
                root.childNodes.pop(-1)
        
        childName = "finally"
        child = doc.createElement(childName)
        child.appendChild(self.doc.createTextNode(str(astnode.lineno)))
        root.appendChild(child)
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
        _ast.Assert			: handleAssert,
        _ast.Attribute		: handleAttribute,
        _ast.Assign			: handleAtomic,
        _ast.AugAssign		: handleAugAssign,
        _ast.BinOp			: handleBinOp,
        _ast.BitAnd			: handleAtomic,
        _ast.BitOr			: handleAtomic,
        _ast.BitXor			: handleAtomic,
        _ast.BoolOp			: handleAtomic,
        _ast.Break			: handleAtomic,
        _ast.Call			: handleCall,
        _ast.ClassDef		: handleClassDef,
        _ast.Compare		: handleCompare,
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
        _ast.Import			: handleImport,
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
        _ast.Print			: handlePrint,
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
    x = xmlConverter(filename, False)
    x.generateXML()
    
    print x.doc.toprettyxml(':   ')
    
    print 'done'