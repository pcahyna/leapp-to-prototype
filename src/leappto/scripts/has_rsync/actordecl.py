from leappto.actor_support.portannotation import PortAnnotation, DstPortAnnotation, InitialPortAnnotation, Any
from leappto.msgtypes.msgtypes import RsyncStatus, Trigger

outports_annotations = {'rsyncstatus': PortAnnotation(RsyncStatus)}

inports_annotations = {'dummystart': DstPortAnnotation(Trigger, Any) }
