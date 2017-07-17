from leappto.actor_support.portannotation import PortAnnotation, DstPortAnnotation, Any
from leappto.msgtypes.msgtypes import ShellCommandStatus

class FooOutput(ShellCommandStatus):
    pass

class FooInput(ShellCommandStatus):
    pass

inports_annotations = {'fooin': DstPortAnnotation(FooInput, Any)}
outports_annotations = {'fooout': PortAnnotation(FooOutput)}

