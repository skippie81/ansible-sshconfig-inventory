import re
import json
import pprint

pp = pprint.PrettyPrinter(indent=4)

class sshConfigInventory:

    ansible_var_names = {
        'user': 'ansible_ssh_user',
        'port': 'ansible_port',
        'identityfile': 'ansible_ssh_private_key_file'
    }

    def __init__(self,global_group='global'):
        self.inventory = {
            '_meta': {
                'hostvars': {}
            }
        }
        self.global_vars = {}
        self.inventory[global_group] = {
            'hosts': [],
            'vars': {}
        }

    def add_group_var(self,group,name,value):
        try:
            self.inventory[group]['vars'][name] = value
        except KeyError:
            return False
        return True

    def groups(self):
        groups = self.inventory.keys()
        pp.pprint(groups)
        return groups

    def get_inventory(self,style='json'):
        if style == 'json':
            return json.dumps(self.inventory,sort_keys=True, indent=4, separators=(',', ': '))

    def read(self,file,ignore_hosts=[]):
        empty_line = re.compile('^[ \s\t]*$')
        host_alias_line = re.compile('^Host .+')
        host_line = re.compile('^Hostname .+')
        user_line = re.compile('^User .+')
        port_line = re.compile('^Port .+')
        identityfile_line = re.compile('^IdentityFile .+')
        inline_instruction = re.compile('^#:.+')

        try:
            hosts = []
            host = {
                'inventory_hostname': None,
                'group' : None,
                'groups': [],
                'children': [],
                'hostvars': {}
            }
            with open(file) as ssh_config:
                for line in ssh_config:
                    if empty_line.match(line):
                        continue
                    line = line.lstrip()
                    line = line.replace("\n",'')
                    line = line.replace("\r",'')
                    line = line.replace("\r\n",'')

                    if host_alias_line.match(line):
                        if host['inventory_hostname'] != None and host['inventory_hostname'] not in ignore_hosts and 'ignore' not in host.keys():
                            hosts.append(host)
                        host = {'inventory_hostname': line.split(' ')[1], 'group' : None, 'groups': [], 'children': [], 'hostvars': {}}

                    elif host_line.match(line):
                        hostname = line.split(' ')[1]
                        host['ansible_hostname'] = hostname

                        try:
                            main_group = '.'.join(hostname.split('.')[1:])
                        except IndexError:
                            main_group = self.global_group

                        if host['group'] == None:
                            host['group'] = main_group

                        try:
                            group_list = hostname.split('.')[2:]
                            while len(group_list) > 0:
                                host['children'].append('.'.join(group_list))
                                group_list.pop()
                        except IndexError:
                            continue

                    elif user_line.match(line):
                        host['hostvars'][self.ansible_var_names['user']] = line.split(' ')[1]
                    elif port_line.match(line):
                        host['hostvars'][self.ansible_var_names['port']] = line.split(' ')[1]
                    elif identityfile_line.match(line):
                        host['hostvars'][self.ansible_var_names['identityfile']] = line.split(' ')[1]
                    elif inline_instruction.match(line):
                        name = line.split(':')[1]
                        try:
                            value = line.split(':')[2]
                        except IndexError:
                            value = True
                        try:
                            if isinstance(host[name],list):
                                host[name].extend(value.split(','))
                            else:
                                host[name] = value
                        except KeyError:
                            host[name] = value
                if host['inventory_hostname'] != None and host['inventory_hostname'] not in ignore_hosts:
                    hosts.append(host)
        except IOError:
            print 'Cloud not open file %s' % file
            self.inventory = {}
            return False

        for host in hosts:
            inventory_hostname = host['inventory_hostname']
            group = host['group']
            if group != None:
                if group not in self.inventory.keys():
                    self.inventory[group] = {
                        'hosts': [],
                        'vars': {},
                        'children': []
                    }
                self.inventory[group]['hosts'].append(inventory_hostname)
            else:
                self.inventory[self.global_group]['hosts'].append(inventory_hostname)

            for other_group in host['children']:
                if other_group not in self.inventory.keys():
                    self.inventory[other_group] = {
                        'hosts': [],
                        'vars': {},
                        'children': []
                    }
                if group not in self.inventory[other_group]['children']:
                    self.inventory[other_group]['children'].append(group)

            for other_group in host['groups']:
                if other_group not in self.inventory.keys():
                    self.inventory[other_group] = {
                        'hosts': [],
                        'vars': {},
                        'children': []
                    }
                self.inventory[other_group]['hosts'].append(inventory_hostname)

            self.inventory['_meta']['hostvars'][inventory_hostname] = host['hostvars']