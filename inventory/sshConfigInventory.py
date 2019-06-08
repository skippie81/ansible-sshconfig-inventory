import re
import json

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
        if style == 'ini':
            return self.ini_inventory()

    def read(self,file,ignore_hosts=[],use_fqdn=False,domain_group_seperator='.'):
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
                        if inventory_hostname in ignore_hosts:
                            inventory_hostname = None
                    elif host_line.match(line) and inventory_hostname != None:
                        hostname = line.split(' ')[1]
                        if use_fqdn:
                            inventory_hostname = hostname
                        if '.' in hostname:
                            base_group = domain_group_seperator.join(hostname.split('.')[1:])
                            groups.append(base_group)
                            try:
                                group_list = hostname.split('.')[2:]
                                while len(group_list) > 0:
                                    group = domain_group_seperator.join(group_list)
                                    self.add_child_to_group(group,base_group)
                                    base_group = group
                                    group_list.pop()
                            except IndexError:
                                continue
                    elif user_line.match(line) or port_line.match(line) or identityfile_line.match(line) and inventory_hostname != None:
                        name = line.split(' ')[0]
                        value = line.split(' ')[1]
                        hostvars[self.ansible_var_names[name.lower()]] = value
                    elif inline_instruction.match(line) and inventory_hostname != None:
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
                if inventory_hostname != None:
                    self.add_to_inventory(inventory_hostname,groups,hostvars)
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
            if inventory_hostname not in self.ini_inventory[group]['hosts']:
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

    def hosts(self,group):
        try:
            return self.inventory[group]['hosts']
        except KeyError:
            return []

    def children(self,group):
        try:
            return self.inventory[group]['children']
        except KeyError:
            return []

    def hostvars(self,host,dict=True):
        try:
            hostvars = self.inventory['_meta']['hostvars'][host]
            if dict:
                return hostvars
            varlist = []
            for name in hostvars.keys():
                varlist.append((name,hostvars[name]))
            return varlist
        except KeyError:
            if dict:
                return {}
            return []

    def groupvars(self,group):
        try:
            varlist = []
            groupvars = self.inventory[group]['vars']
            for name in groupvars.keys():
                varlist.append((name,groupvars[name]))
            return varlist
        except KeyError:
            return []

    def ini_inventory(self):
        ini = '# generated by inventory.py\n'
        for group in self.groups():
            first = True
            for host in self.hosts(group):
                if first:
                    ini += '[%s]\n' % group
                    first = False
                ini += '{0:<35}'.format(host)
                for (name,value) in self.hostvars(host,False):
                    ini += '{0:<30} '.format('%s=%s' % (name,value))
                ini += '\n'
            if not first:
                ini += '\n'
            first = True
            for (name,value) in self.groupvars(group):
                if first:
                    ini += '[%s:vars]\n' %  group
                    first = False
                ini += '%s=%s\n' % (name,value)
            if not first:
                ini += '\n'
            first = True
            for child in self.children(group):
                if first:
                    ini += '[%s:children]\n' % group
                    first = False
                ini += '%s\n' % child
            if not first:
                ini += '\n'
        return ini