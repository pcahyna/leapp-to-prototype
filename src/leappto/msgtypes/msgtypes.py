from leappto.actor_support.portannotation import MsgType

class Trigger(MsgType):
    def __init__(self):
	super(Trigger, self).__init__(None, None, None)

class ShellCommandStatus(MsgType):
    def __init__(self, srcname, errorinfo, retcode):
        super(ShellCommandStatus, self).__init__(srcname, errorinfo, retcode)

class DockerStatus(ShellCommandStatus):
    pass

class RsyncStatus(ShellCommandStatus):
    pass

class RsyncExecStatus(ShellCommandStatus):
    pass

class DockerInfoStatus(ShellCommandStatus):
    pass

class ConnectivityStatus(ShellCommandStatus):
    pass

class DockerListStatus(ShellCommandStatus):
    pass
    
