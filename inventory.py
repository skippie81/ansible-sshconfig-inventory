#!/usr/bin/env python

import argparse
import ConfigParser
import os
import inspect
import json
from inventory import sshConfigInventory

settings = {
    'config_file': 'inventory.cfg',
    'ssh_config': {
        'ssh_config_file': os.path.join(os.getenv('HOME','~/'),'.ssh/config'),
        'ignore_hosts': []
    },
    'defaults': {
        'group_seperator': '_'
    }
}

ssh_inventory = sshConfigInventory()

def configure():
    config = ConfigParser.ConfigParser()
    inspect.getfile(inspect.currentframe())
    path = os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe())))
    config_file = os.path.join(path,settings['config_file'])
    try:
        config.read(config_file)
        for section in config.sections():
            groupname = section
            if ':' in section:
                groupname = section.split(':')[0]
            for name,value in config.items(section):
                if ',' in value:
                    value = value.split(',')
                try:
                    if name in settings[groupname].keys():
                        if isinstance(settings[groupname][name],list):
                            value = [ value ]
                except KeyError:
                    settings[groupname] = {}
                settings[groupname][name] = value
    except ConfigParser.Error:
        return False
    return True

# main part of the program
def read(ssh_config,use_fqdn=False,domain_group_seperator='.'):
    ssh_inventory.read(ssh_config,settings['ssh_config']['ignore_hosts'],use_fqdn=use_fqdn,domain_group_seperator=domain_group_seperator)
    for group in ssh_inventory.groups():
        if group in settings.keys():
            for name in settings[group].keys():
                ssh_inventory.add_group_var(group,name,settings[group][name])

if __name__ == '__main__':
    # read configuration file
    configure()

    # ceate the argument parser
    parser = argparse.ArgumentParser(description='Dynamic ansible inventory with ssh_config as source')
    parser.add_argument('-l','--list',action='store_true',help='output inventory json format')
    parser.add_argument('--host',type=str,nargs=1,help='get hostvars of a host')
    parser.add_argument('-H',action='store_true',help='Print human readable ini style invenotry')
    parser.add_argument('--version',action='version',version='%(prog)s v0.0.1')
    parser.add_argument('--fqdn',action='store_true',help='use fqdn in inventory')
    parser.add_argument('--group_seperator',type=str,nargs=1,help='Group seperator char for domain subgroups',default=settings['defaults']['group_seperator'])
    parser.add_argument('--ssh-config-file',type=str,nargs=1,help='Path to ssh config file',default=settings['ssh_config']['ssh_config_file'])

    # parse the arguments
    args = parser.parse_args()

    style = 'json'
    if args.list:
        style='json'
    if args.H:
        style='ini'

    # read the .ssh/config
    read(args.ssh_config_file,use_fqdn=args.fqdn,domain_group_seperator=args.group_seperator[0])

    # output
    if args.host != None:
        hostvars = ssh_inventory.hostvars(args.host[0])
        print json.dumps(hostvars,sort_keys=True, indent=4, separators=(',', ': '))
    else:
        print ssh_inventory.get_inventory(style)
