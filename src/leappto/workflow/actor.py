""" Actors able to execute checks on our workflow """

from __future__ import print_function

import os
from importlib import import_module
from subprocess import Popen, PIPE
from wowp.actors import FuncActor
import leappto.actor_support.portannotation
from leappto.actor_support.portannotation import ActorError, MsgType
from leappto.msgtypes.msgtypes import ShellCommandStatus

class PrereqError(ActorError):
    def __init__(self, errmsg, prereqname, errdetails):
        super(PrereqError, self).__init__("skipped", errmsg, errdetails)
        self.prereqname = prereqname

class ScriptError(ActorError):
    pass
    
class AnnotatedFuncActor(FuncActor):
    def __init__(self, outports_annotations, inports_annotations, func, args=(), kwargs={}, outports=None, inports=None, name=None):
        super(AnnotatedFuncActor, self).__init__(func, args, kwargs, outports=outports, inports=inports, name=name)
        for ipn in self.inports.keys():
            self.inports[ipn].annotation = inports_annotations[ipn]
        for opn in self.outports.keys():
            self.outports[opn].annotation = outports_annotations[opn]


class LoadedAnnotatedFuncActor(AnnotatedFuncActor):
    def __init__(self, modname, func=None, args=(), kwargs={}, outports=None, inports=None, name=None):
        self.annmodule = import_module(modname)
        oa = self.annmodule.__dict__['outports_annotations']
        try:
            ia = self.annmodule.__dict__['inports_annotations']
        except KeyError:
            ia = None
        super(LoadedAnnotatedFuncActor,
              self).__init__(oa, ia,
                             self.annmodule.__dict__['func'] if func==None else func,
                             args, kwargs, outports=outports, inports=inports, name=name)


class DirAnnotatedFuncActor(LoadedAnnotatedFuncActor):

    ACTOR_PREFIX = 'leappto.scripts.'

    def __init__(self, pkgname, func=None, args=(), kwargs={}, outports=None, inports=None, name=None):
        modname = self.ACTOR_PREFIX + pkgname + '.actordecl'

        super(DirAnnotatedFuncActor, self).__init__(modname, func, args, kwargs, outports=outports, inports=inports, name=name)
        actor_path = os.path.dirname(os.path.abspath(self.annmodule.__file__))

lfa = LoadedAnnotatedFuncActor('leappto.scripts.fooactor', lambda fooin: fooin, outports=('fooout'))
dfa = DirAnnotatedFuncActor('baractor', lambda fooin: fooin, outports=('fooout'))

class DirAnnotatedShellActor(DirAnnotatedFuncActor):

    def __init__(self, pkgname, target_cmd, script, args=(), kwargs={}, outports=None, inports=None, name=None):
        def allfunc(*inportargs):
            try:
                preres = self.prefunc(self.inports, inportargs)
                try:
                    res = self.execfunc(preres)
                except Exception as ee:
                    raise ScriptError("failed", "script execution failed", ee)

            except ActorError as ae:
                if len(self.outports) == 1:
                    excres = self.outports.at(0).annotation.msgtype(self.name, ae, None)
                else:
                    excres = tuple(port.annotation.msgtype(self.name, ae, None) for port in self.outports )
                return excres

            return self.postfunc(res)

        self._target_cmd = target_cmd
        self.prefunc = self._default_prefunc
        self.postfunc = self._default_postfunc
        self.script = script
 
        super(DirAnnotatedShellActor, self).__init__(pkgname, allfunc, args, kwargs, outports, inports, name)

    def _default_prefunc(self, _, inportargs):
        print ("prefunc:", self.name)
        for a in inportargs:
            if isinstance(a, MsgType):
                if a.errorinfo is not None:
                    raise PrereqError("required actor failed", a.srcname, a.errorinfo)
                if isinstance(a, ShellCommandStatus):
                    if a.payload != 0:
                        raise PrereqError("required actor returned a nonzero exit code", a.srcname, a.payload)
        return ()

    # for now we do not do anything with the input arguments (no way to pass them to the script itself)
    def execfunc(self, _):
        """ Method that should be executed by actor"""
        print ("execfunc:", self.name)
        script_input = open(self.script)
        child = Popen(self._target_cmd, stdin=script_input, stdout=PIPE, stderr=PIPE)
        out, err = child.communicate()
        return (child.returncode, out, err)

    def _default_postfunc(self, res):
        return self.outports.values()[0].annotation.msgtype(self.name, None, res[0])

