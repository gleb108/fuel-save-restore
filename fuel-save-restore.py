#!/usr/bin/env python

from fuelclient import v1 as fuel
import yaml
import argparse

nodecl = fuel.node.get_client()
envcl = fuel.environment.get_client()
netcl = fuel.network_group.get_client()

def get_nodes(env_id=False):
    data = nodecl.get_all()
    if env_id:
        return [node for node in data if node['cluster'] == env_id]
    else:
        return data

def get_env(env_id=False):
    if env_id:
        return envcl.get_by_id(env_id)
    else:
        return envcl.get_all()


def get_networks(env_id=False):
    data = netcl.get_all()
    if env_id:
        return [net for net in data if net['group_id'] == env_id]
    else:
        return data


def yaml_store(data, filename):
    file = open(filename, 'w+')
    file.write(yaml.safe_dump(data))
    print "Backup is stored to {0}".format(filename)
    file.close()


def yaml_load(filename):
    file = open(filename)
    read_y = yaml.load(file.read())
    file.close()
    return read_y


def backup_env(env_id):
    nodes = get_nodes(env_id)
    networks = get_networks(env_id)
    return {'nodes':nodes, 'networks':networks}

def restore_networks(env_id, data):
    print "Restore Networks"
    networks = get_networks(env_id)
    safe_keys = ['cidr', 'gateway', 'meta']
    for net in networks:
        print(net['name'])
        for saved_net in data:
            if net['name'] == saved_net['name']:
                netcl.update(net['id'], **{k: saved_net[k] for k in safe_keys})


def restore_nodes(env_id, data):
    print "Restore Nodes"
    nodes = get_nodes(env_id)
    safe_keys = ['hostname', 'labels', 'name']
    for node in nodes:
        for saved_node in data:
            if node['mac'] == saved_node['mac']:
                print(node['mac'])
                if args.update_hostnames and saved_node['name'] != saved_node['hostname']:
                    saved_node['hostname'] = saved_node['name']
                    print "hostname => {0}".format(saved_node['hostname'])
                else:
                    safe_keys.remove('hostname')
                nodecl.update(node['id'], **{k: saved_node[k] for k in safe_keys})


parser = argparse.ArgumentParser()
parser.add_argument('-e', '--env', action="store", default=False, type=int, dest="env", help="Specify the environment id")
parser.add_argument('-f', '--file', action="store", dest="filename", default='backup.yaml', help="File to save/restore node names")
parser.add_argument('-s', '--save', action="store_true", default=False, dest="save", help="Save nodes and networks data")
parser.add_argument('--restore-nodes', action="store_true", default=False, dest="restore_nodes", help="Restore only nodes for the environment")
parser.add_argument('--restore-networks', action="store_true", default=False, dest="restore_networks", help="Restore only networks for the environment")
parser.add_argument('-r', '--restore', action="store_true", default=False, dest="restore", help="Restore all nodes and networks for the environment")
parser.add_argument('-u', '--update-hostnames', action="store_true", default=False, dest="update_hostnames", help="Update hostnames in accordance with names")

args = parser.parse_args()


if args.restore:
    args.save = False
    args.restore_nodes = True
    args.restore_networks = True

if args.restore_nodes or args.restore_networks:
    data = yaml_load(args.filename)

if args.restore_nodes:
    restore_nodes(args.env, data['nodes'])

if args.restore_networks:
    restore_networks(args.env, data['networks'])

if args.save:
    if (args.env and args.filename == 'backup.yaml'):
       filename = "backup-env-{0}.yaml".format(args.env)
    else:
       filename = args.filename 
    yaml_store(backup_env(args.env), filename)

