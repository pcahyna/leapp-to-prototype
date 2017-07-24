from leappto.actor_support.portannotation import PortAnnotation, DstPortAnnotation, InitialPortAnnotation, Any
from leappto.msgtypes.msgtypes import DockerStatus, DockerListStatus, Trigger

outports_annotations = {'docker_status': PortAnnotation(DockerStatus)}
