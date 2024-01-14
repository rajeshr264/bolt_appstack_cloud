#!/usr/bin/env python3

import json
import sys 
import urllib3

def create_vm(proxmox_node,clone_id, post_data):
    """Create the VM"""  
    #taskid = proxmox_node.qemu(clone_id).clone.create(**post_data)
    msg = " Created " + post_data['name'] + " with id = " + post_data['newid']
    print(msg)
    return msg

def start_vm(proxmox_node,post_data):
    """Start VM"""
    msg = " Starting " + post_data['name']
    #output_result = proxmox_node.qemu().start.put()

def execute():
    """Gets the list of nodes to create"""
    try:
        from proxmoxer import ProxmoxAPI
        HAS_PROXMOXER = True
    except ImportError:
        print("Eror: proxmoxer python module not found.")
        exit(1)

    params = json.load(sys.stdin)
    # print("params : ")
    # print(params)

    # for debugging
    #out_file = open("inventory_test2.json", "w") 
    #json.dump(params, out_file, indent = 6) 
    #out_file.close() 
    #exit(1)
    # with open('inventory_test2.json') as f:
    #     params = json.load(f)
    
    proxmox = ProxmoxAPI(params['_target']['uri'], user=params['_target']['user'], password= params['_target']['password'], verify_ssl=False)
    #print(proxmox.access.users.get()) # for debug purposes

    # get the apps node from inventory file
    import yaml
    with open(params['apps_stack_filename']) as file:
        apps_stacks_yaml = yaml.safe_load(file)

    #print(apps_stacks_yaml)
    apps = apps_stacks_yaml['apps']
    msg = ""
    proxmox_node = proxmox.nodes(params['_target']['name'])  
    for app in apps:
        # iterate through the apps list
        clone_id = app['clone_id']
        if 'count' in app:  
            for i in range(app['count'] ):
                vm_name_array = app['name'].split('.')
                vm_name = vm_name_array.pop(0)+ "-" + str(i) + '.'
                vm_name += '.'.join(vm_name_array)
                post_data = {
                  "name": vm_name,
                  "newid":  proxmox.cluster.nextid.get(),
                  "storage": 'local-lvm',
                  "full": 1
                }
                # create a VM
                msg += create_vm(proxmox_node,clone_id, post_data)
                #start the VM
                start_vm(proxmox_node, post_data)
                # get its ip address

        else:
            post_data = {
                  "name": app['name'],
                  "newid":  proxmox.cluster.nextid.get(),
                  "storage": 'local-lvm',
                  "full": 1
            }
            msg += create_vm(proxmox_node,clone_id,post_data)
            #start the VM
            start_vm(proxmox_node, post_data)

    return {'Message': msg}

urllib3.disable_warnings() # stop https warnings
node_info = execute()
#print(node_info)
