# ansible-sshconfig-inventory
Use your .ssh/config as source for ansible inventory

Will create an inventory containng all your hosts in your ssh config file. 

## Usage

in ansible.cfg
```
[defaults]
inventory = '<path>/inventory.py'
```

## Configuration

inventory.cfg accepts the following options

|section|name|value| default | |
|-------|:--:|:---:|---------|-|
|ssh_config|ssh_config_file| string | ~/.ssh/config ||
||ignore_hosts| string[,string[,...]] | None | List of hosts not to include in inventory |
|inventory|global_group| string | global | groupname for hosts not having a fqdn hostname |

example:
```
[ssh_config]
ssh_config_file: /home/myusername/.ssh/config
ignore_hosts: github.com

[inventory]
global_group: global
```

## Options

In the ssh configuration file you can add special instructions. Lines starting with 
__\#\:__ are evaluated by the inventory script and applied to the first host line above this line.

__Syntax:__
```
#:<keyword>[:<value>[:value]]
```

|keyword|value| |
|:-----:|:---:|-|
|ignore|n/a|ignore this host in inventory|
|group|string|set the main group name for this host|
|groups|string[,string[,...]]|extra groups where to add the host to|
