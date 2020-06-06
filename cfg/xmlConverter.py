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
    BUILTINFUNCS = set( # a set of python's builtin functions, that are not imported or defined
                i.strip() for i in """
                    hasattr
                    lower
                """.split())
    BUILTINMODS = set( # a set of python's builtin modules, that are not imported or defined
                    i.strip() for i in """
                        ArgImagePlugin
                        Audio_mac
                        BaseHTTPServer
                        Bastion
                        BdfFontFile
                        BmpImagePlugin
                        BufrStubImagePlugin
                        CGIHTTPServer
                        Canvas
                        Carbon
                        CodeWarrior
                        ColorPicker
                        ConfigParser
                        ContainerIO
                        Cookie
                        Crypto
                        CurImagePlugin
                        Cython
                        DcxImagePlugin
                        Dialog
                        DocXMLRPCServer
                        EasyDialogs
                        EpsImagePlugin
                        ExifTags
                        Explorer
                        FileDialog
                        Finder
                        FitsStubImagePlugin
                        FixTk
                        FliImagePlugin
                        FontFile
                        FpxImagePlugin
                        FrameWork
                        GbrImagePlugin
                        GdImageFile
                        GifImagePlugin
                        GimpGradientFile
                        GimpPaletteFile
                        Gnuplot
                        GribStubImagePlugin
                        HTMLParser
                        Hdf5StubImagePlugin
                        IN
                        IPython
                        IcnsImagePlugin
                        IcoImagePlugin
                        ImImagePlugin
                        Image
                        ImageChops
                        ImageCms
                        ImageColor
                        ImageDraw
                        ImageDraw2
                        ImageEnhance
                        ImageFile
                        ImageFileIO
                        ImageFilter
                        ImageFont
                        ImageGL
                        ImageGrab
                        ImageMath
                        ImageMode
                        ImageOps
                        ImagePalette
                        ImagePath
                        ImageQt
                        ImageSequence
                        ImageShow
                        ImageStat
                        ImageTk
                        ImageTransform
                        ImageWin
                        ImtImagePlugin
                        IptcImagePlugin
                        JpegImagePlugin
                        MacOS
                        McIdasImagePlugin
                        MicImagePlugin
                        MimeWriter
                        MiniAEFrame
                        MpegImagePlugin
                        MspImagePlugin
                        Nav
                        Netscape
                        OSATerminology
                        OleFileIO
                        PIL
                        PSDraw
                        PaletteFile
                        PalmImagePlugin
                        PcdImagePlugin
                        PcfFontFile
                        PcxImagePlugin
                        PdfImagePlugin
                        PixMapWrapper
                        PixarImagePlugin
                        PngImagePlugin
                        PpmImagePlugin
                        PsdImagePlugin
                        PyQt4
                        Pycluster
                        Queue
                        ScrolledText
                        SgiImagePlugin
                        SimpleDialog
                        SimpleHTTPServer
                        SimpleXMLRPCServer
                        SocketServer
                        SpiderImagePlugin
                        StdSuites
                        StringIO
                        SunImagePlugin
                        SystemEvents
                        TarIO
                        Terminal
                        TgaImagePlugin
                        TiffImagePlugin
                        TiffTags
                        Tix
                        Tkconstants
                        Tkdnd
                        Tkinter
                        UserDict
                        UserList
                        UserString
                        VBoxPython2_5
                        VBoxPython2_6
                        VBoxPython2_7
                        WalImageFile
                        WmfImagePlugin
                        XVThumbImagePlugin
                        XbmImagePlugin
                        XpmImagePlugin
                        _AE
                        _AH
                        _App
                        _CF
                        _CG
                        _CarbonEvt
                        _Cm
                        _Ctl
                        _Dlg
                        _Drag
                        _Evt
                        _File
                        _Fm
                        _Folder
                        _Help
                        _IBCarbon
                        _Icn
                        _LWPCookieJar
                        _Launch
                        _List
                        _Menu
                        _Mlte
                        _MozillaCookieJar
                        _OSA
                        _Qd
                        _Qdoffs
                        _Qt
                        _Res
                        _Scrap
                        _Snd
                        _TE
                        _Win
                        __builtin__
                        __future__
                        _abcoll
                        _ast
                        _bisect
                        _bsddb
                        _builtinSuites
                        _codecs
                        _codecs_cn
                        _codecs_hk
                        _codecs_iso2022
                        _codecs_jp
                        _codecs_kr
                        _codecs_tw
                        _collections
                        _csv
                        _ctypes
                        _ctypes_test
                        _curses
                        _curses_panel
                        _elementtree
                        _functools
                        _hashlib
                        _heapq
                        _hotshot
                        _imaging
                        _imagingft
                        _imagingmath
                        _imagingtk
                        _io
                        _json
                        _locale
                        _lsprof
                        _multibytecodec
                        _multiprocessing
                        _pyio
                        _random
                        _scproxy
                        _socket
                        _sqlite3
                        _sre
                        _ssl
                        _strptime
                        _struct
                        _symtable
                        _testcapi
                        _threading_local
                        _tkinter
                        _warnings
                        _weakref
                        _weakrefset
                        abc
                        aepack
                        aetools
                        aetypes
                        aifc
                        antigravity
                        anydbm
                        applesingle
                        appletrawmain
                        appletrunner
                        argparse
                        argvemulator
                        array
                        ast
                        asynchat
                        asyncore
                        atexit
                        audiodev
                        audioop
                        autoGIL
                        autoreload
                        base64
                        bdb
                        bgenlocations
                        binascii
                        binhex
                        bisect
                        blessings
                        bsddb
                        buildtools
                        bundlebuilder
                        bz2
                        cPickle
                        cProfile
                        cStringIO
                        calendar
                        cfmfile
                        cgi
                        cgitb
                        cheesecake
                        chunk
                        cmath
                        cmd
                        code
                        codecs
                        codeop
                        collections
                        colorsys
                        commands
                        compileall
                        compiler
                        contextlib
                        contract
                        cookielib
                        copy
                        copy_reg
                        crypt
                        csv
                        ctypes
                        ctypes_configure
                        curses
                        cython
                        cythonmagic
                        datetime
                        dateutil
                        dateutils
                        dbhash
                        dbm
                        decimal
                        decorator
                        difflib
                        dircache
                        dis
                        distutils
                        doctest
                        docutils
                        dumbdbm
                        dummy_thread
                        dummy_threading
                        easy_install
                        email
                        encodings
                        errno
                        exceptions
                        fcntl
                        filecmp
                        fileinput
                        findertools
                        fnmatch
                        formatter
                        fpformat
                        fractions
                        ftplib
                        functools
                        future_builtins
                        gc
                        genericpath
                        gensuitemodule
                        gestalt
                        getopt
                        getpass
                        gettext
                        glob
                        grp
                        gzip
                        hashlib
                        heapq
                        hmac
                        hotshot
                        htmlentitydefs
                        htmllib
                        httplib
                        ic
                        icglue
                        icopen
                        idlelib
                        ihooks
                        imageutils
                        imaplib
                        imghdr
                        imp
                        importlib
                        imputil
                        inspect
                        io
                        itertools
                        jinja2
                        json
                        keyword
                        lib2to3
                        linecache
                        locale
                        logging
                        lxml
                        macerrors
                        macostools
                        macpath
                        macresource
                        macurl2path
                        mailbox
                        mailcap
                        markupbase
                        marshal
                        math
                        matplotlib
                        md5
                        mechanize
                        mhlib
                        mimetools
                        mimetypes
                        mimify
                        mmap
                        modulefinder
                        mpl_toolkits
                        multifile
                        multiprocessing
                        mutex
                        netrc
                        new
                        nis
                        nntplib
                        nose
                        ntpath
                        nturl2path
                        numbers
                        numpy
                        octavemagic
                        opcode
                        operator
                        optparse
                        os
                        os2emxpath
                        pandas
                        parallelmagic
                        paramiko
                        parser
                        pdb
                        pickle
                        pickletools
                        pimp
                        pip
                        pipes
                        pkg_resources
                        pkgutil
                        platform
                        plistlib
                        popen2
                        poplib
                        posix
                        posixfile
                        posixpath
                        pprint
                        profile
                        pstats
                        pty
                        pwd
                        py_compile
                        pycallgraph
                        pyclbr
                        pydoc
                        pydoc_data
                        pyexpat
                        pygame
                        pygments
                        pygraphviz
                        pykalman
                        pylab
                        pymc
                        pyparsing
                        pytz
                        pyximport
                        quantities
                        quopri
                        random
                        re
                        readline
                        repr
                        requests
                        resource
                        rexec
                        rfc822
                        rlcompleter
                        rmagic
                        robotparser
                        runpy
                        runsnakerun
                        sched
                        scikits
                        scipy
                        select
                        selenium
                        sets
                        setuptools
                        sgmllib
                        sha
                        shelve
                        shlex
                        shutil
                        signal
                        sip
                        sipconfig
                        sipdistutils
                        site
                        six
                        skimage
                        sklearn
                        smtpd
                        smtplib
                        sndhdr
                        socket
                        sphinx
                        sphinx_pypi_upload
                        sqlite3
                        squaremap
                        sre
                        sre_compile
                        sre_constants
                        sre_parse
                        ssl
                        stat
                        statsmodels
                        statvfs
                        storemagic
                        string
                        stringold
                        stringprep
                        strop
                        struct
                        subprocess
                        sunau
                        sunaudio
                        symbol
                        sympyprinting
                        symtable
                        sys
                        sysconfig
                        syslog
                        tabnanny
                        tarfile
                        telnetlib
                        tempfile
                        terminalcommand
                        termios
                        test
                        tests
                        textwrap
                        this
                        thread
                        threading
                        time
                        timeit
                        tkColorChooser
                        tkCommonDialog
                        tkFileDialog
                        tkFont
                        tkMessageBox
                        tkSimpleDialog
                        toaiff
                        token
                        tokenize
                        tornado
                        trace
                        traceback
                        ttk
                        tty
                        turtle
                        types
                        unicodedata
                        unittest
                        urllib
                        urllib2
                        urlparse
                        user
                        uu
                        uuid
                        vboxapi
                        vboxshell
                        videoreader
                        warnings
                        wave
                        weakref
                        webbrowser
                        whichdb
                        wsgiref
                        wx
                        wxhack
                        wxversion
                        xdrlib
                        xml
                        xmllib
                        xmlrpclib
                        xxsubtype
                        zipfile
                        zipimport
                        zlib
                        zmq
                    """.split()
                )

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
        try:
            if astnode.func.id in self.BUILTINFUNCS:
                for arg in itertools.chain(astnode.args, (kw.value for kw in astnode.keywords)):
                    if not self.handleNode(doc, root, arg):
                        root.childNodes.pop(-1)
                return 1
        except AttributeError:
            try:
                if astnode.func.attr in self.BUILTINFUNCS:
                    return 1
            except AttributeError:
                pass

        if isinstance(astnode.func, _ast.Attribute):	# this is an imported function
            self.handleAttribute(doc, root, astnode.func)
        else:
            for arg in itertools.chain(astnode.args, (kw.value for kw in astnode.keywords)):
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
#				for node in self.FUNCTIONS["%s.%s" %(self.modname, astnode.func.id)].body:
#					if not self.handleNode(doc, root, node):
#						root.childNodes.pop(-1)
            else:
                childName = "functioncall"
                child = doc.createElement(childName)
                if not isinstance(astnode, _ast.Module):
                    label = str(self.FUNCTIONS["%s.%s" %(self.modname if self.modname else "module", astnode.func.id)].lineno)
                    child.appendChild(self.doc.createTextNode(label))
                root.appendChild(child)

                return 1
#				root.appendChild(self.doc.createTextNode("loopback to %s" %astnode.func.id))

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

    def handleGeneratorExp(self, doc, parent, astnode):
        pass

    def handleGlobal(self, doc, parent, astnode):
        pass

    def handleGtE(self, doc, parent, astnode):
        pass

    def handleIf(self, doc, root, astnode):
        # new code
        if not self.handleNode(doc, root, astnode.test):
            root.childNodes.pop(-1)
        # /new code
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

        for node in (n for n in astnode.body if isinstance(n, _ast.FunctionDef)):
            self.FUNCTIONS["%s.%s" %(self.modname, self.funcname if self.funcname else node.name)] = node

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
        child.appendChild(self.doc.createTextNode(str(astnode.finalbody[0].lineno-1)))
        root.appendChild(child)
        for node in astnode.finalbody:
            if not self.handleNode(doc, child, node):
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
        # _ast.AST: handleAst,
        # _ast.Add: handleAdd,
        # _ast.And: handleAnd,
        # _ast.AnnAssign: handleAnnassign,
        _ast.Assert: handleAssert,
        _ast.Assign: handleAssign,
        # _ast.AsyncFor: handleAsyncfor,
        # _ast.AsyncFunctionDef: handleAsyncfunctiondef,
        # _ast.AsyncWith: handleAsyncwith,
        _ast.Attribute: handleAttribute,
        # _ast.AugAssign: handleAugassign,
        # _ast.AugLoad: handleAugload,
        # _ast.AugStore: handleAugstore,
        # _ast.Await: handleAwait,
        # _ast.BinOp: handleBinop,
        # _ast.BitAnd: handleBitand,
        # _ast.BitOr: handleBitor,
        # _ast.BitXor: handleBitxor,
        # _ast.BoolOp: handleBoolop,
        # _ast.Break: handleBreak,
        _ast.Call: handleCall,
        # _ast.ClassDef: handleClassdef,
        _ast.Compare: handleCompare,
        _ast.Constant: handleAtomic,
        _ast.Continue: handleContinue,
        _ast.Del: handleDel,
        _ast.Delete: handleDelete,
        _ast.Dict: handleDict,
        # _ast.DictComp: handleDictcomp,
        # _ast.Div: handleDiv,
        _ast.Eq: handleAtomic,
        # _ast.ExceptHandler: handleExcepthandler,
        _ast.Expr: handleExpr,
        # _ast.Expression: handleExpression,
        # _ast.ExtSlice: handleExtslice,
        # _ast.FloorDiv: handleFloordiv,
        # _ast.For: handleFor,
        # _ast.FormattedValue: handleFormattedvalue,
        _ast.FunctionDef: handleFunctionDef,
        # _ast.FunctionType: handleFunctiontype,
        # _ast.GeneratorExp: handleGeneratorexp,
        _ast.Global: handleGlobal,
        # _ast.Gt: handleGt,
        # _ast.GtE: handleGte,
        _ast.If: handleIf,
        # _ast.IfExp: handleIfexp,
        _ast.Import: handleImport,
        _ast.ImportFrom: handleImportFrom,
        # _ast.In: handleIn,
        _ast.Index: handleIndex,
        _ast.Interactive: handleInteractive,
        _ast.Invert: handleInvert,
        # _ast.Is: handleIs,
        # _ast.IsNot: handleIsnot,
        # _ast.JoinedStr: handleJoinedstr,
        # _ast.LShift: handleLshift,
        _ast.Lambda: handleLambda,
        _ast.List: handleList,
        # _ast.ListComp: handleListcomp,
        _ast.Load: handleLoad,
        # _ast.Lt: handleLt,
        # _ast.LtE: handleLte,
        # _ast.MatMult: handleMatmult,
        # _ast.mod: handleMod,
        _ast.Module: handleModule,
        # _ast.Mult: handleMult,
        _ast.Name: handleName,
        # _ast.NamedExpr: handleNamedexpr,
        # _ast.Nonlocal: handleNonlocal,
        # _ast.Not: handleNot,
        # _ast.NotEq: handleNoteq,
        # _ast.NotIn: handleNotin,
        # _ast.Or: handleOr,
        _ast.Param: handleParam,
        # _ast.Pass: handlePass,
        # _ast.Pow: handlePow,
        # _ast.RShift: handleRshift,
        # _ast.Raise: handleRaise,
        _ast.Return: handleReturn,
        _ast.Set: handleSet,
        # _ast.SetComp: handleSetcomp,
        _ast.slice: handleSlice,
        # _ast.Starred: handleStarred,
        # _ast.Store: handleStore,
        _ast.Sub: handleSub,
        _ast.Subscript: handleSubscript,
        _ast.Suite: handleSuite,
        # _ast.Try: handleTry,
        _ast.Tuple: handleTuple,
        # _ast.TypeIgnore: handleTypeignore,
        # _ast.UAdd: handleUadd,
        # _ast.USub: handleUsub,
        # _ast.UnaryOp: handleUnaryop,
        _ast.While: handleWhile,
        _ast.With: handleWith,
        # _ast.Yield: handleYield,
        # _ast.YieldFrom: handleYieldfrom,
        # _ast.alias: handleAlias,
        # _ast.arg: handleArg,
        # _ast.arguments: handleArguments,
        # _ast.cmpop: handleCmpop,
        # _ast.comprehension: handleComprehension,
        # _ast.excepthandler: handleExcepthandler,
        # _ast.keyword: handleKeyword,
        # _ast.Mod: handleMod,
        # _ast.operator: handleOperator,
        _ast.Slice: handleSlice,
        # _ast.stmt: handleStmt,
        # _ast.type_ignore: handleType_Ignore,
        # _ast.unaryop: handleUnaryop,
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
