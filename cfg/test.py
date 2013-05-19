#import utils as ut
#import utils
#from utils import nodeType as nt
#from utils import nodeType
from utils import *

#def bar():
#	print 'hi'
#	if 3==4:
#		print 'yay'
#	else:
#		print 'oh no'
#	3+4
#	return 5

#def bar():
#	print 'entring'
#	for i in L:
#		print i
#	else:
#		print 'hi'
#	print 'ending'

def bar():
#	nt('')
	nodeType('')
#	utils.nodeType('')
#	ut.nodeType('')
	print 'hi'
	try:
		1+1
	except AttributeError:
		print 'oops'
	else:
		print 'woo hoo'
	finally:
		if 3>4:
			print 'phew'
			print 'uhh'
		else:
			print 'ahh'
	print 'done'
#	bar()
#bar()

#def bar():
#	a += 1
#	for x in [1,2]:
#		print x
#		if x%2:
#			print x**2
#			break
#		else:
#			print x**3
#	else:
#		print "wpp"
#	print "done"
#bar()
#
#assert(1==bar())

#def add(a, b):
#    return a + b
#
#
#def mult(a, b):
#    result = 0
#    for i in range(b):
#        result += add(result, a)
#    return result
#
#def foo(x):
#    if x%2==1:
#        print x, 'is odd'
#    elif x%2==0:
#        print x, 'is even'
#    else:
#    	print 'this should never be reached'

#
#if __name__ == "__main__":
#    print 'starting'
#    mult(3,5)
#    print 'done'

#if __name__ == "__main__":
#	import trace, sys
#	tracer = trace.Trace(count=False, trace=True, ignoredirs=[sys.prefix, sys.exec_prefix])
#	r = tracer.run('bar()')