from leappto.actor_support.portannotation import PortAnnotation, DstPortAnnotation, Any

class FooOutput(object):
    pass

class FooInput(object):
    pass

input_annotations = {'fooin': DstPortAnnotation(FooInput, Any)}
output_annotations = {'fooout': PortAnnotation(FooOutput)}

