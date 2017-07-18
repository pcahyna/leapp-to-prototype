from leappto.actor_support.portannotation import PortAnnotation, DstPortAnnotation, Any
from leappto.msgtypes.msgtypes import RsyncStatus, RsyncExecStatus

inports_annotations = {'has_rsync': DstPortAnnotation(RsyncStatus, Any)}
outports_annotations = {'rsync_exec_status': PortAnnotation(RsyncExecStatus)}

