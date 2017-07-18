from leappto.actor_support.portannotation import PortAnnotation, DstPortAnnotation, Any
from leappto.msgtypes.msgtypes import DockerStatus, DockerListStatus

inports_annotations = {'has_docker': DstPortAnnotation(DockerStatus, Any)}
outports_annotations = {'docker_list_status': PortAnnotation(DockerListStatus)}

