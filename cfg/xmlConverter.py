import _ast
import importlib
import itertools

from setuptools import glob
from xml.dom.minidom import Document
import collections
import sys
import os

class xmlConverter(object):

    FUNCTIONS = {}
    IMPORTS = collections.defaultdict(lambda : None) # also functions as the import stack to avoid expanding redundant imports
    IMPORT_FILES = set()
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

        self.BUILTINFUNCS = set(  # a set of python's builtin functions, that are not imported or defined
                                i.strip() for i in dir(__builtins__)
                            )


    def findModuleFile(self, modname):
        if modname.endswith('.py'): modname = modname.rsplit('.',1)[0]
        modname = modname.rsplit('.',1)[-1]
        fpath = importlib.util.find_spec(modname).origin
        self.IMPORT_FILES.add(fpath)


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

        if not isinstance(astnode, _ast.Call): handle = False

        if handle:
            for node in self.FUNCTIONS["%s.%s" %(modname, funcname)].body:
                if not self.handleNode(doc, root, self.FUNCTIONS["%s.%s" %(modname, funcname)]):
                    root.childNodes.pop(-1)
        else:
            root.appendChild(self.doc.createTextNode("loopback to %s" %funcname))

        if popcall:
            self.callstack.pop(-1)


    def handleAssign(self, doc, root, astnode):
        if not self.handleNode(doc, root, astnode.value):
            root.childNodes.pop(-1)
        return 1


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

        if not self.handleNode(doc, root, astnode.right):
            root.childNodes.pop(-1)

        if not self.handleNode(doc, root, astnode.op):
            root.childNodes.pop(-1)

        return 1


    def handleBoolOp(self, doc, root, astnode):

        for node in astnode.values:
            if not self.handleNode(doc, root, node):
                root.childNodes.pop(-1)
        if not self.handleNode(doc, root, astnode.op):
            root.childNodes.pop(-1)

        return 1


    def handleCall(self, doc, root, astnode):

        for arg in itertools.chain(astnode.args, (kw.value for kw in astnode.keywords)):
            if not self.handleNode(doc, root, arg):
                root.childNodes.pop(-1)

        if hasattr(astnode.func, 'id') and astnode.func.id in self.BUILTINFUNCS:
            return 1

        elif hasattr(astnode.func, 'attr') and astnode.func.attr in self.BUILTINFUNCS:
            return 1

        if isinstance(astnode.func, _ast.Attribute):	# this is an imported function
            self.handleAttribute(doc, root, astnode.func)
        else:

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
                childName = "functioncall"
                child = doc.createElement(childName)
                if not isinstance(astnode, _ast.Module):
                    if astnode.func.id == 'print':
                        label = str(astnode.lineno)
                    else:
                        label = str(self.FUNCTIONS["%s.%s" %(self.modname if self.modname else "module", astnode.func.id)].lineno)
                    child.appendChild(self.doc.createTextNode(label))
                root.appendChild(child)

                return 1

            else:
                childName = "functioncall"
                child = doc.createElement(childName)
                if not isinstance(astnode, _ast.Module):
                    if astnode.func.id == 'print':
                        label = str(astnode.lineno)
                    else:
                        label = str(self.FUNCTIONS["%s.%s" %(self.modname if self.modname else "module", astnode.func.id)].body[0].lineno)
                    child.appendChild(self.doc.createTextNode(label))
                root.appendChild(child)

                return 1
        return 1


    def handleClassDef(self, doc, parent, astnode):
        for node in astnode.body:
            if not self.handleNode(doc, parent, node):
                parent.childNodes.pop(-1)

        return 1


    def handleCompare(self, doc, root, astnode):

        for node in itertools.chain([astnode.left] if hasattr(astnode, 'left') else [],
                                    [astnode.right] if hasattr(astnode, 'right') else [],
                                    astnode.comparators):
            if not self.handleNode(doc, root, node):
                root.childNodes.pop(-1)

        for op in astnode.ops:
            if not self.handleNode(doc, root, op):
                root.childNodes.pop(-1)

        return 1

    def handleDelete(self, doc, parent, astnode):
        for node in astnode.targets:
            if not self.handleNode(doc, parent, node):
                parent.childNodes.pop(-1)

        return 1


    def handleDict(self, doc, parent, astnode):
        for k,v in zip(astnode.keys, astnode.values):
            if not self.handleNode(doc, parent, k):
                parent.childNodes.pop(-1)
            if not self.handleNode(doc, parent, v):
                parent.childNodes.pop(-1)

        return 1


    def handleDictComp(self, doc, parent, astnode):
        for node in astnode.generators:
            if not self.handleNode(doc, parent, node):
                parent.childNodes.pop(-1)

        if not self.handleNode(doc, parent, astnode.key):
            parent.childNodes.pop(-1)
        if not self.handleNode(doc, parent, astnode.value):
            parent.childNodes.pop(-1)

        return 1


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


    def handleNamedExpr(self, doc, root, astnode):
        if not self.handleNode(self.doc, root, astnode.value):
            root.childNodes.pop(-1)

        if not self.handleNode(self.doc, root, astnode.target):
            root.childNodes.pop(-1)

        return 1


    def handleExtSlice(self, doc, parent, astnode):
        pass


    def handleLoop(self, doc, root, astnode):

        if hasattr(astnode, "iter"): self.handleNode(doc, root, astnode.iter)
        if hasattr(astnode, 'target'): self.handleNode(doc, root, astnode.target)

        for node in astnode.body:
            if not self.handleNode(doc, root, node):
                root.childNodes.pop(-1)

        childName = "else"
        child = doc.createElement(childName)
        try:
            childTitle = str(min((node.lineno for node in astnode.orelse if hasattr(node, 'lineno')))-1)
        except ValueError:
            childTitle = '-'
        child.appendChild(self.doc.createTextNode(childTitle))
#		child.appendChild(self.doc.createTextNode(max('-', str(min((node.lineno for node in astnode.orelse if hasattr(node, 'lineno')))-1) )))
        root.appendChild(child)
        for node in astnode.orelse:
            if not self.handleNode(doc, child, node):
                child.childNodes.pop(-1)

        return 1

    def handleFunctionDef(self, doc, root, astnode):
        self.callstack.append("%s.%s" %(self.modname if self.modname else "module", astnode.name))
        self.FUNCTIONS["%s.%s" %(self.modname, self.funcname if self.funcname else astnode.name)] = astnode

        for node in itertools.chain(astnode.args.defaults, astnode.args.kw_defaults):
            if not self.handleNode(doc, root, node):
                root.childNodes.pop(-1)

        for node in astnode.body:
            if not self.handleNode(doc, root, node):
                root.childNodes.pop(-1)
        self.callstack.pop(-1)
        return 1


    def handleReturn(self, doc, root, astnode):
        if not self.handleNode(doc, root, astnode.value):
            root.childNodes.pop(-1)

        return 1



    def handleGlobal(self, doc, parent, astnode):
        pass


    def handleIf(self, doc, root, astnode):
        if not self.handleNode(doc, root, astnode.test):
            root.childNodes.pop(-1)
        if not isinstance(astnode.body, list): astnode.body = [astnode.body]
        for node in astnode.body:
            if not self.handleNode(doc, root, node):
                root.childNodes.pop(-1)

        childName = "else"
        child = doc.createElement(childName)
        if astnode.orelse:
            if not isinstance(astnode.orelse, list): astnode.orelse = [astnode.orelse]
            child.appendChild(self.doc.createTextNode(max('-', str(min((node.lineno for node in astnode.orelse if hasattr(node, 'lineno')))-1) )))
            root.appendChild(child)
            for node in astnode.orelse:
                if not self.handleNode(doc, child, node):
                    child.childNodes.pop(-1)

        return 1

    def handleImport(self, doc, root, astnode): # TODO: Expand class and function defs inline
        for imported in astnode.names:
            self.IMPORT_FILES.add(self.findModuleFile(imported.name))
            if not imported.asname:
                imported.asname = imported.name
            modname, asname = imported.name, imported.asname

            self.IMPORT_FILES.add(self.findModuleFile(modname))

            if modname in self.MODULES: # module has been imported before (possibly under a different alias)
                if self.MODULES[modname] == asname: # module has been imported before under the same alias
                    root.appendChild(self.doc.createTextNode("Repeat import of %s as %s skipped" %(imported.name, imported.asname)))
                else: # module has been imported before under a different alias
                    if asname in self.IMPORTS: # module is being imported under a previously used alias
                        self.MODULES.pop(modname)
                        if not self.MODULES[modname]:
                            self.MODULES.pop(modname)

                        self.IMPORTS[asname] = modname

                    else:
                        self.IMPORTS[asname] = modname
                        self.MODULES[modname].add(asname)
                        addFuncs = {}
                        for funcname,func in self.FUNCTIONS.items():
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
        self.IMPORT_FILES.add(self.findModuleFile(astnode.module))
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
        if not self.handleNode(doc, parent, astnode.value):
            parent.childNodes.pop(-1)

        return 1


    def handleInteractive(self, doc, parent, astnode):
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
        for g in astnode.generators:
            if not self.handleNode(doc, parent, g):
                parent.childNodes.pop(-1)

        if not self.handleNode(doc, parent, astnode.elt):
            parent.childNodes.pop(-1)

        return 1


    def handleComprehension(self, doc, parent, astnode):
        if not self.handleNode(doc, parent, astnode.iter):
            parent.childNodes.pop(-1)

        for node in astnode.ifs:
            if not self.handleNode(doc, parent, node):
                parent.childNodes.pop(-1)

        return 1


    def handleLoad(self, doc, parent, astnode):
        pass


    def handleModule(self, doc, root, astnode):

        root.appendChild(self.doc.createTextNode(str(0)))

        for node in (n for n in astnode.body if isinstance(n, _ast.FunctionDef)):
            self.FUNCTIONS["%s.%s" %(self.modname, self.funcname if self.funcname else node.name)] = node

        for node in astnode.body:
            # handle only functiondefs and classdefs in an imported module. Handle everything in the main (executed) module
            if not self.imported or any((isinstance(astnode, astype) for astype in [_ast.Module, _ast.FunctionDef, _ast.ClassDef])):
                if not self.handleNode(doc, root, node):
                    child.childNodes.pop(-1)

        return 1


    def handleParam(self, doc, parent, astnode):
        pass


    def handleRepr(self, doc, root, astnode):

        if not self.handleNode(doc, root, astnode.value):
            root.childNodes.pop(-1)

        return 1


    def handleSlice(self, doc, root, astnode):
        if astnode.lower is not None and not self.handleNode(doc, root, astnode.lower):
            root.childNodes.pop(-1)
        if astnode.lower is not None and not self.handleNode(doc, root, astnode.step if astnode.step else _ast.Num(1)):
            root.childNodes.pop(-1)
        if astnode.lower is not None and not self.handleNode(doc, root, astnode.upper):
            root.childNodes.pop(-1)

        return 1


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

    def handleTry(self, doc, root, astnode):

        for node in astnode.body:
            if not self.handleNode(doc, root, node):
                root.childNodes.pop(-1)

        for handler in astnode.handlers:
            childName = "except {}".format(handler.type.id)
            child = doc.createElement(childName)
            child.appendChild(self.doc.createTextNode(str(handler.lineno)))
            root.appendChild(child)

            for node in handler.body:
                if not self.handleNode(doc, child, node):
                    child.childNodes.pop(-1)

        if astnode.orelse:
            childName = 'exceptElse'
            child = doc.createElement(childName)
            child.appendChild(self.doc.createTextNode(str(astnode.finalbody[0].lineno)))
            root.appendChild(child)
            for node in astnode.orelse:
                if not self.handleNode(doc, child, node):
                    child.childNodes.pop(-1)

        if astnode.finalbody:
            childName = "finally"
            child = doc.createElement(childName)
            child.appendChild(self.doc.createTextNode(str(astnode.finalbody[0].lineno)))
            root.appendChild(child)
            for node in astnode.finalbody:
                if not self.handleNode(doc, child, node):
                    child.childNodes.pop(-1)

        return 1


    def handleRaise(self, doc, parent, astnode):
        if not self.handleNode(doc, parent, astnode.exc):
            parent.childNodes.pop(-1)

        return 1


    def handleTuple(self, doc, parent, astnode):
        pass


    def handleUnaryOp(self, doc, root, astnode):
        if not self.handleNode(doc, root, astnode.operand):
            root.childNodes.pop(-1)

        if not self.handleNode(doc, root, astnode.op):
            root.childNodes.pop(-1)

        return 1


    def handleWith(self, doc, parent, astnode):
        pass

    def handlealias(self, doc, parent, astnode):
        pass

    def handlearguments(self, doc, parent, astnode):
        pass


    def handlecmpop(self, doc, parent, astnode):
        pass


    def handleexpr_context(self, doc, parent, astnode):
        pass

    def handlekeyword(self, doc, parent, astnode):
        pass

    def handleMod(self, doc, parent, astnode):
        pass

    def handleoperator(self, doc, parent, astnode):
        pass


    def handlestmt(self, doc, parent, astnode):
        pass

    def handleunaryop(self, doc, parent, astnode):
        pass

    HANDLERS = {
        _ast.Import: handleImport,
        _ast.ImportFrom: handleImportFrom,
        # _ast.AST: handleAst,
        _ast.Constant: handleAtomic,
        _ast.Add: handleAtomic,
        _ast.Sub: handleAtomic,
        _ast.Mult: handleAtomic,
        _ast.Div: handleAtomic,
        _ast.Mod: handleAtomic,
        _ast.FloorDiv: handleAtomic,
        _ast.Pow: handleAtomic,

        _ast.UAdd: handleAtomic,
        _ast.USub: handleAtomic,

        _ast.Name: handleAtomic,
        _ast.Expr: handleExpr,
        _ast.Assign: handleAssign,
        _ast.AugAssign: handleAugAssign,
        _ast.NamedExpr: handleNamedExpr,
        # _ast.AnnAssign: handleAnnassign,
        _ast.Delete: handleDelete,

        _ast.Compare: handleCompare,
        _ast.Assert: handleAssert,
        # _ast.AsyncFor: handleAsyncfor,
        # _ast.AsyncFunctionDef: handleAsyncfunctiondef,
        # _ast.AsyncWith: handleAsyncwith,
        _ast.Attribute: handleAttribute,
        # _ast.AugLoad: handleAugload,
        # _ast.AugStore: handleAugstore,
        # _ast.Await: handleAwait,
        _ast.BinOp: handleBinOp,
        _ast.UnaryOp: handleUnaryOp,
        _ast.BoolOp: handleBoolOp,

        _ast.BitAnd: handleAtomic,
        _ast.BitOr: handleAtomic,
        _ast.BitXor: handleAtomic,
        _ast.Invert: handleAtomic,

        _ast.LShift: handleAtomic,
        _ast.RShift: handleAtomic,

        _ast.For: handleLoop,
        _ast.While: handleLoop,
        _ast.Break: handleAtomic,
        _ast.Continue: handleAtomic,
        _ast.Pass: handleAtomic,

        _ast.List: handleList,
        _ast.Dict: handleDict,
        _ast.Set: handleList,
        _ast.Subscript: handleSubscript,
        _ast.slice: handleSlice,
        _ast.Index: handleIndex,

        _ast.comprehension: handleComprehension,
        _ast.GeneratorExp: handleListComp,
        _ast.ListComp: handleListComp,
        _ast.SetComp: handleListComp,
        _ast.DictComp: handleDictComp,

        _ast.Eq: handleAtomic,
        _ast.NotEq: handleAtomic,
        _ast.Gt: handleAtomic,
        _ast.GtE: handleAtomic,
        _ast.Lt: handleAtomic,
        _ast.LtE: handleAtomic,

        _ast.Is: handleAtomic,
        _ast.IsNot: handleAtomic,

        _ast.In: handleAtomic,
        _ast.NotIn: handleAtomic,

        _ast.And: handleAtomic,
        _ast.Or: handleAtomic,
        _ast.Not: handleAtomic,

        _ast.If: handleIf,
        _ast.IfExp: handleIf,

        _ast.FunctionDef: handleFunctionDef,
        _ast.Return: handleReturn,
        _ast.Yield: handleReturn,
        _ast.YieldFrom: handleReturn,
        _ast.Call: handleCall,

        _ast.ClassDef: handleClassDef,

        _ast.Try: handleTry,
        _ast.ExceptHandler: handleExceptHandler,
        _ast.Raise: handleRaise,

        # _ast.Del: handleAtomic,
        # _ast.Expression: handleExpression,
        # _ast.ExtSlice: handleExtslice,
        # _ast.FormattedValue: handleFormattedvalue,
        # _ast.FunctionType: handleFunctiontype,
        # _ast.Global: handleGlobal,

        # _ast.Interactive: handleInteractive,
        # _ast.JoinedStr: handleJoinedstr,
        # _ast.Lambda: handleLambda,
        # _ast.Load: handleLoad,
        # _ast.MatMult: handleMatmult,
        _ast.Module: handleModule,
        # _ast.Nonlocal: handleNonlocal,
        # _ast.Param: handleParam,
        # _ast.Starred: handleStarred,
        # _ast.Store: handleStore,
        # _ast.Suite: handleSuite,
        # _ast.Tuple: handleTuple,
        # _ast.TypeIgnore: handleTypeignore,
        # _ast.With: handleWith,
        # _ast.alias: handleAlias,
        # _ast.arg: handleArg,
        # _ast.arguments: handleArguments,
        # _ast.cmpop: handleCmpop,
        # _ast.keyword: handleKeyword,
        # _ast.operator: handleOperator,
        # _ast.stmt: handleStmt,
        # _ast.type_ignore: handleType_Ignore,
        # _ast.withitem: handleWithitem,
    }


if __name__ == "__main__":
    filename = 'test.py'
    print('starting')

    d = Document()
    x = xmlConverter(filename, False)
    x.generateXML()

    with open('output.xml', 'w') as f:
        f.write(x.doc.toprettyxml('	'))
    print(x.doc.toprettyxml(':   '))

    print(*x.IMPORT_FILES, sep='\n')

    print('done')
