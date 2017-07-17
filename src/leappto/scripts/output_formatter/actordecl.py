from __future__ import print_function

from leappto.actor_support.portannotation import PortAnnotation, DstPortAnnotation, All
from leappto.scripts.msgtypes.msgtypes import ShellCommandStatus

inports_annotations = {'allstat': DstPortAnnotation(ShellCommandStatus, All)}
outports_annotations = {'msg': FinalPortAnnotation}

def func(allstat):
    msg += '{'
    for m in allstat.values():
        if m.errorinfo == None:
            msg += m.srcname + ':' + m.payload + ',\n'
        else:
            msg += m.strname + ':' + m.errorinfo.__str__() + ',\n'

    msg += '}'
    return msg

def outports=('msg')
