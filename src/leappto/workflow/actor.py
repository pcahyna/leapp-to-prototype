""" Actors able to execute checks on our workflow """

from __future__ import print_function

import os
from importlib import import_module
from subprocess import Popen
from wowp.actors import FuncActor
import leappto.actor_support.portannotation


class CheckActor(FuncActor):
    """ A check actor that can be part of our workflow """
    DEFAULT_IN = 'default_in'

    def __init__(self, check_name, check_script, output_path, requires=None):
        self._check_name = check_name
        self._check_script = check_script
        self._requires = requires

        if not os.path.exists(output_path):
            os.makedirs(output_path)

        self._stdout_file = os.path.join(output_path,
                                         self.check_name + '_stdout.txt')
        self._stderr_file = os.path.join(output_path,
                                         self.check_name + '_stderr.txt')

        self._target_cmd = None

        if self.requires:
            super(CheckActor, self).__init__(self.__func_with_requirement,
                                             inports=[CheckActor.DEFAULT_IN,
                                                      self.requires],
                                             outports=[self.check_name+'_out'])
        else:
            super(CheckActor, self).__init__(self.__func,
                                             inports=[CheckActor.DEFAULT_IN],
                                             outports=[self.check_name+'_out'])

    @property
    def check_name(self):
        """ Return actors name """
        return self._check_name

    @property
    def check_script(self):
        """ Return script that should be executed """
        return self._check_script

    @property
    def check_stdout_file(self):
        """ Return path for file containing check standard output """
        return self._stdout_file

    @property
    def check_stderr_file(self):
        """ Return path for file containing check standard error output """
        return self._stderr_file

    @property
    def requires(self):
        """ Return list of requires for this actor """
        return self._requires

    def __func(self, _):
        """ Method that should be executed by actor without requires"""
        script_fd = open(self.check_script, 'r')
        stdout_fd = open(self.check_stdout_file, 'w+')
        stderr_fd = open(self.check_stderr_file, 'w+')
        child = Popen(self._target_cmd,
                      stdin=script_fd,
                      stdout=stdout_fd,
                      stderr=stderr_fd)
        child.communicate()
        return child.returncode

    def __func_with_requirement(self, _, req_rc):
        """ Method that should be executed by actor with requires"""
        if req_rc:
            print(self.check_name +
                  ": [ERROR] Requirement failed: " +
                  self.requires)
            return 1

        script_fd = open(self.check_script, 'r')
        stdout_fd = open(self.check_stdout_file, 'w+')
        stderr_fd = open(self.check_stderr_file, 'w+')
        child = Popen(self._target_cmd,
                      stdin=script_fd,
                      stdout=stdout_fd,
                      stderr=stderr_fd)
        child.communicate()
        return child.returncode

    def set_target_cmd(self, target_cmd):
        """ Build command that will be executed on target machine """
        self._target_cmd = target_cmd

class AnnotatedFuncActor(FuncActor):
    def __init__(self, outports_annotations, inports_annotations, func, args=(), kwargs={}, outports=None, inports=None, name=None):
        super(AnnotatedFuncActor, self).__init__(func, args, kwargs, outports=outports, inports=inports, name=name)
        for ipn in self.inports.keys():
            self.inports[ipn].annotation = inports_annotations[ipn]
        for opn in self.outports.keys():
            self.outports[opn].annotation = outports_annotations[opn]


class LoadedAnnotatedFuncActor(AnnotatedFuncActor):
    def __init__(self, modname, func, args=(), kwargs={}, outports=None, inports=None, name=None):
        self.annmodule = import_module(modname)
        oa = self.annmodule.__dict__['outports_annotations']
        ia = self.annmodule.__dict__['inports_annotations']
        super(LoadedAnnotatedFuncActor, self).__init__(oa, ia, func, args, kwargs, outports=outports, inports=inports, name=name)


class DirectoryAnnotatedFuncActor(LoadedAnnotatedFuncActor):

    ACTOR_PREFIX = 'leappto.scripts.'

    def __init__(self, pkgname, func, args=(), kwargs={}, outports=None, inports=None, name=None):
        modname = self.ACTOR_PREFIX + pkgname + '.actordecl'

        super(DirectoryAnnotatedFuncActor, self).__init__(modname, func, args, kwargs, outports=outports, inports=inports, name=name)
        actor_path = os.path.dirname(os.path.abspath(self.annmodule.__file__))

lfa = LoadedAnnotatedFuncActor('leappto.scripts.fooactor', lambda fooin: fooin, outports=('fooout'))
dfa = DirectoryAnnotatedFuncActor('baractor', lambda fooin: fooin, outports=('fooout'))
