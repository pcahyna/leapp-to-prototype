from __future__ import print_function

from leappto.actor_support.portannotation import PortAnnotation, DstPortAnnotation, FinalPortAnnotation, All
from leappto.msgtypes.msgtypes import ShellCommandStatus

inports_annotations = {'allstat': DstPortAnnotation(ShellCommandStatus, All)}
outports_annotations = {'msg': FinalPortAnnotation}

def func(allstat):
    print (repr(allstat.values()))
    msg = '{'
    for m in allstat.values():
        print(repr(m))
        if m.errorinfo == None:
            msg += m.srcname + ':' + m.payload.__str__() + ',\n'
        else:
            msg += m.srcname + ':' + m.errorinfo.__str__() + ',\n'

    msg += '}'
    return msg

outports=('msg')
