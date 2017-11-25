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
        self.global_group = global_group
        self.inventory[global_group] = {
            'hosts': [],
            'vars': {},
            'children': []
        }

    def add_group_var(self,group,name,value):
        try:
            self.inventory[group]['vars'][name] = value
        except KeyError:
            return False
        return True

    def groups(self):
        groups = self.inventory.keys()
        i = groups.index('_meta')
        del groups[i]
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
            with open(file) as ssh_config_file:
                inventory_hostname = None
                groups = []
                hostvars = {}
                for line in ssh_config_file:
                    if empty_line.match(line):
                        continue
                    line = line.lstrip()
                    line = line.replace("\n",'')
                    line = line.replace("\r",'')
                    line = line.replace("\r\n",'')
                    if host_alias_line.match(line):
                        if inventory_hostname != None:
                            self.add_to_inventory(inventory_hostname,groups,hostvars)
                            inventory_hostname = None
                            groups = []
                            hostvars = {}
                        inventory_hostname = line.split(' ')[1]
                    elif host_line.match(line):
                        hostname = line.split(' ')[1]
                        if '.' in hostname:
                            base_group = '.'.join(hostname.split('.')[1:])
                            groups.append(base_group)
                            try:
                                group_list = hostname.split('.')[2:]
                                while len(group_list) > 0:
                                    group = '.'.join(group_list)
                                    self.add_child_to_group(group,base_group)
                                    base_group = group
                                    group_list.pop()
                            except IndexError:
                                continue
                    elif user_line.match(line) or port_line.match(line) or identityfile_line.match(line):
                        name = line.split(' ')[0]
                        value = line.split(' ')[1]
                        hostvars[self.ansible_var_names[name.lower()]] = value
                    elif inline_instruction.match(line):
                        name = line.split(':')[1]
                        try:
                            value = line.split(':')[2]
                        except IndexError:
                            value = None
                        if name == 'ignore' and value == None:
                            inventory_hostname = None
                        elif name == 'groups' and value != None:
                            groups.extend(value.split(','))
                        else:
                            hostvars[name] = value
        except IOError:
            print 'Cloud not open file %s' % file
            self.inventory = {}
            return False


    def add_to_inventory(self,inventory_hostname,groups,hostvars):
        for group in groups:
            if group not in self.inventory.keys():
                self.inventory[group] = {
                    'hosts': [],
                    'vars': {},
                    'children': []
                }
            self.inventory[group]['hosts'].append(inventory_hostname)
        self.inventory['_meta']['hostvars'][inventory_hostname] = hostvars

    def add_child_to_group(self,group,child):
        if group not in self.inventory.keys():
            self.inventory[group] = {
                'hosts': [],
                'vars': {},
                'children': []
            }
        if child not in self.inventory[group]['children']:
            self.inventory[group]['children'].append(child)