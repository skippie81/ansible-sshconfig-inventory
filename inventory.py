#!/usr/bin/env python

import json
import argparse
import ConfigParser
import os
from inventory import sshConfigInventory

settings = {
    'config_file': 'inventory.cfg',
    'ssh_config': {
        'ssh_config_file': os.path.join(os.getenv('HOME','~/'),'.ssh/config'),
        'ignore_hosts': []
    }
}

def configure():
    config = ConfigParser.ConfigParser()
    try:
        config.read(settings['config_file'])
        for section in config.sections():
            groupname = section
            if ':' in section:
                groupname = section.split(':')[0]
            for name,value in config.items(section):
                try:
                    if ',' in value:
                        settings[groupname][name] = value.split(',')
                    if isinstance(settings[groupname][name],list):
                        settings[groupname][name].append(value)
                    else:
                        settings[groupname][name] = value
                except KeyError:
                    settings[groupname] = {}
                    settings[groupname][name] = value
    except ConfigParser.Error:
        return False
    print settings
    return True

# main part of the program
def main(style='json'):
    ssh_inventory = sshConfigInventory()
    ssh_inventory.read(settings['ssh_config']['ssh_config_file'],settings['ssh_config']['ignore_hosts'])
    for group in ssh_inventory.groups():
        if group in settings.keys():
            for name in settings[group].keys():
                ssh_inventory.add_group_var(group,name,settings[group][name])
    print ssh_inventory.get_inventory()

if __name__ == '__main__':
    # ceate the argument parser
    parser = argparse.ArgumentParser(description='Dynamic ansible inventory with ssh_config as source')
    parser.add_argument('-l','--list',action='store_true',help='output ')
    parser.add_argument('--host',type=str,nargs=1,help='get hostvars of a host')
    parser.add_argument('-H',action='store_true',help='Print human readable ini style invenotry')
    parser.add_argument('--version',action='version',version='%(prog)s 0.0.1-beta1')

    # parse the arguments
    args = parser.parse_args()

    # read configuration file
    configure()
    main()