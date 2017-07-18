from leappto.actor_support.portannotation import PortAnnotation, DstPortAnnotation, InitialPortAnnotation, Any
from leappto.msgtypes.msgtypes import ConnectivityStatus, Trigger

outports_annotations = {'connectivity_status': PortAnnotation(ConnectivityStatus)}

inports_annotations = {'dummystart': DstPortAnnotation(Trigger, Any) }