"""LeApp CLI implementation"""

from argparse import ArgumentParser
from leappto.providers.libvirt_provider import LibvirtMachineProvider
from json import dumps
from os import getuid
import os.path
from subprocess import Popen, PIPE, check_output, CalledProcessError
import sys

from wowp.actors import FuncActor, DictionaryMerge


def main():
    if getuid() != 0:
        print("Please run me as root")
        exit(-1)


    ap = ArgumentParser()
    ap.add_argument('-v', '--version', action='store_true', help='display version information')
    parser = ap.add_subparsers(help='sub-command', dest='action')

    list_cmd = parser.add_parser('list-machines', help='list running virtual machines and some information')
    migrate_cmd = parser.add_parser('migrate-machine', help='migrate source VM to a target container host')

    list_cmd.add_argument('--shallow', action='store_true', help='Skip detailed scans of VM contents')
    list_cmd.add_argument('pattern', nargs='*', default=['*'], help='list machines matching pattern')

    def _port_spec(arg):
        """Converts a port forwarding specifier to a (host_port, container_port) tuple

        Specifiers can be either a simple integer, where the host and container port are
        the same, or else a string in the form "host_port:container_port".
        """
        host_port, sep, container_port = arg.partition(":")
        host_port = int(host_port)
        if sep is None:
            container_port = host_port
        else:
            container_port = int(container_port)
        return host_port, container_port

    migrate_cmd.add_argument('machine', help='source machine to migrate')
    migrate_cmd.add_argument('-t', '--target', default=None, help='target VM name')
    migrate_cmd.add_argument('--identity', default=None, help='Path to private SSH key')
    migrate_cmd.add_argument(
        '--tcp-port',
        default=None,
        dest="forwarded_ports",
        nargs='*',
        type=_port_spec,
        help='Target ports to forward to macrocontainer (temporary!)'
    )


    def _find_machine(ms, name):
        for machine in ms:
            if machine.hostname == name:
                return machine
        return None


    class MigrationContext:
        def __init__(self, target, target_cfg, disk, forwarded_ports=None):
            self.target = target
            self.target_cfg = target_cfg
            self.disk = disk
            if forwarded_ports is None:
                forwarded_ports = [(80, 80)] # Default to forwarding plain HTTP
            else:
                forwarded_ports = list(forwarded_ports)
            forwarded_ports.append((9022, 22)) # Always forward SSH
            self.forwarded_ports = forwarded_ports

        @property
        def _ssh_base(self):
            return ['ssh'] + self.target_cfg + ['-4', self.target]

        def _ssh(self, cmd, **kwargs):
            arg = self._ssh_base + [cmd]
            print(arg)
            return Popen(arg, **kwargs).wait()

        def _ssh_sudo(self, cmd, **kwargs):
            return self._ssh("sudo bash -c '{}'".format(cmd), **kwargs)

        def copy(self):
            proc = Popen(['virt-tar-out', '-a', self.disk, '/', '-'], stdout=PIPE)
            return self._ssh('cat > /opt/leapp-to/container.tar.gz', stdin=proc.stdout)

        def start_container(self, img, init):
            command = 'docker rm -f container 2>/dev/null 1>/dev/null ; rm -rf /opt/leapp-to/container ; mkdir -p /opt/leapp-to/container && ' + \
                    'tar xf /opt/leapp-to/container.tar.gz -C /opt/leapp-to/container && ' + \
                    'docker run -tid' + \
                    ' -v /sys/fs/cgroup:/sys/fs/cgroup:ro'
            good_mounts = ['bin', 'etc', 'home', 'lib', 'lib64', 'media', 'opt', 'root', 'sbin', 'srv', 'usr', 'var']
            for mount in good_mounts:
                command += ' -v /opt/leapp-to/container/{m}:/{m}:Z'.format(m=mount)
            for host_port, container_port in self.forwarded_ports:
                command += ' -p {:d}:{:d}'.format(host_port, container_port)
            command += ' --name container ' + img + ' ' + init
            return self._ssh_sudo(command)

        def _fix_container(self, fix_str):
            return self._ssh_sudo('docker exec -t container {}'.format(fix_str))

        def fix_upstart(self):
            fixer = 'bash -c "echo ! waiting ; ' + \
                    'sleep 2 ; ' + \
                    'mkdir -p /var/log/httpd && ' + \
                    'service mysqld start && ' + \
                    'service httpd start"'
            return self._fix_container(fixer)

        def fix_systemd(self):
            # systemd cleans /var/log/ and mariadb & httpd can't handle that, might be a systemd bug
            fixer = 'bash -c "echo ! waiting ; ' + \
                    'sleep 2 ; ' + \
                    'mkdir -p /var/log/{httpd,mariadb} && ' + \
                    'chown mysql:mysql /var/log/mariadb && ' + \
                    'systemctl enable httpd mariadb ; ' + \
                    'systemctl start httpd mariadb"'
            return self._fix_container(fixer)

    def initparam(source, target):
        lmp = LibvirtMachineProvider()
        machines = lmp.get_machines()

        machine_src = _find_machine(machines, source)
        machine_dst = _find_machine(machines, target)

        if not machine_dst or not machine_src:
            print("Machines are not ready:")
            print("Source: " + repr(machine_src))
            print("Target: " + repr(machine_dst))
            exit(-1)


        print('! configuring SSH keys')
        ip = machine_dst.ip[0]
        target_ssh_config = [
                '-o User=vagrant',
                '-o StrictHostKeyChecking=no',
                '-o PasswordAuthentication=no',
                '-o IdentityFile=' + parsed.identity,
        ]

        return (ip, target_ssh_config, machine_src.disks[0].host_path, machine_src.installation.os.version)

    def forwports(forwarded_ports_param):
        if forwarded_ports_param is None:
            forwarded_ports = [(80, 80)] # Default to forwarding plain HTTP
        else:
            forwarded_ports = list(forwarded_ports_param)
        forwarded_ports.append((9022, 22)) # Always forward SSH
        return forwarded_ports

    def sshbase_helper(target, target_cfg):
        return ['ssh'] + target_cfg + ['-4', target]

    def ssh_helper(target, target_cfg, cmd, **kwargs):
        arg = sshbase_helper(target, target_cfg) + [cmd]
        return Popen(arg, **kwargs).wait()


    initparam_actor=FuncActor(initparam, outports=('ip', 'target_cfg', 'disk', 'srcver'))

    forwports_actor=FuncActor(forwports, outports=('forwports'))

    sourcegen_actor=FuncActor(lambda disk: ['virt-tar-out', '-a', disk, '/', '-'], outports=('popenarg') )

    createdest_actor=FuncActor(lambda target, target_cfg, srccmd:
                               ssh_helper(target, target_cfg, 'cat > /opt/leapp-to/container.tar.gz',
                                          stdin=Popen(srccmd, stdout=PIPE).stdout))

    mcparams_actor=DictionaryMerge(inport_names=("ip", 'target_cfg', 'disk'), outport_name="mcparams")

    parsed = ap.parse_args()
    if parsed.action == 'list-machines':
        lmp = LibvirtMachineProvider(parsed.shallow)
        print(dumps({'machines': [m._to_dict() for m in lmp.get_machines()]}, indent=3))

    elif parsed.action == 'migrate-machine':
        if not parsed.identity:
            raise ValueError("Migration requires path to private SSH key to use (--identity)")

        if not parsed.target:
            print('! no target specified, creating leappto container package in current directory')
            # TODO: not really for now
            raise NotImplementedError
        else:
            source = parsed.machine
            target = parsed.target
            forwarded_ports = parsed.forwarded_ports

            print('! looking up "{}" as source and "{}" as target'.format(source, target))

            #ip, target_cfg, disk, srcver = initparam(source, target)
            #mc = MigrationContext(ip, target_cfg, disk)
            print('! copying over')

            sourcegen_actor.inports['disk'] += initparam_actor.outports['disk']
            mcparams_actor.inports['disk'] += initparam_actor.outports['disk']

            createdest_actor.inports['target'] += initparam_actor.outports['ip']
            mcparams_actor.inports['ip'] += initparam_actor.outports['ip']

            createdest_actor.inports['target_cfg'] += initparam_actor.outports['target_cfg']
            mcparams_actor.inports['target_cfg'] += initparam_actor.outports['target_cfg']

            createdest_actor.inports['srccmd'] += sourcegen_actor.outports['popenarg']
            copywf=createdest_actor.get_workflow()
            #copywf.add_outport(initparam_actor.outports['srcver'])
            #copywf.add_outport(initparam_actor.outports['ip'])
            #copywf.add_outport(initparam_actor.outports['disk'])
            #copywf.add_outport(initparam_actor.outports['target_cfg'])
            print('! copying over')
            res=copywf(source=source, target=target)
            srcver=res['srcver'][0]
            mcparams=res['mcparams'][0]

            print(res)

            #ver=copywf.outports['srcver'].pop()
            print(srcver)
            mc = MigrationContext(
                mcparams["ip"],
                mcparams['target_cfg'],
                mcparams['disk'],
                forwarded_ports
            )
            #print(res['ip'][0])
            #print(res['disk'][0])
            #print(res['target_cfg'][0])


            # mc.copy()
            print('! provisioning ...')
            # if el7 then use systemd
            if srcver.startswith('7'):
                result = mc.start_container('centos:7', '/usr/lib/systemd/systemd --system')
                print('! starting services')
                mc.fix_systemd()
            else:
                result = mc.start_container('centos:6', '/sbin/init')
                print('! starting services')
                mc.fix_upstart()
            print('! done')
            sys.exit(result)
