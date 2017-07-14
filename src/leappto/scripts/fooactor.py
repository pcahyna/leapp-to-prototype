from leappto.actor_support.portannotation import PortAnnotation, DstPortAnnotation, Any

class FooOutput(object):
    pass

class FooInput(object):
    pass

inports_annotations = {'fooin': DstPortAnnotation(FooInput, Any)}
outports_annotations = {'fooout': PortAnnotation(FooOutput)}

