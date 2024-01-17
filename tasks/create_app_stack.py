#!/usr/bin/env python3

import json
import sys 
import urllib3
import time 
from paramiko import SSHClient, AutoAddPolicy

# 
generated_inventory = {}

# Wait for the VM to be ready
def wait_for_vm_ready(proxmox_node, vmid, expected_status):
    while True:
        # Get VM status
        vm_status = proxmox_node.qemu(vmid).status.current().get()

        # Check if the VM is stopped/running
        if vm_status.get('lock') == None and vm_status.get('status') == expected_status:
            break 

        # If the VM is not running, wait for a few seconds before checking again
        time.sleep(4)

def create_vm(proxmox_node,clone_id, post_data):
    """Create the VM"""  
    taskid = proxmox_node.qemu(clone_id).clone.create(**post_data)
    msg = " Created " + post_data['name'] + " with id = " + post_data['newid']

    # Call the function to wait for VM readiness
    time.sleep(4)
    wait_for_vm_ready(proxmox_node, post_data['newid'], 'stopped')    
    return msg

def start_vm(proxmox_node,post_data):
    """Start VM"""
    msg = " Starting " + post_data['name']
    proxmox_node.qemu(post_data['newid']).status.start.post()
    wait_for_vm_ready(proxmox_node, post_data['newid'],'running')
    time.sleep(20)
    return msg

def get_ip_address(params, post_data):
    """Get IP Address of VM via QEMU Guest agent & QEMU CLI cmd on PVE Host"""
    # QEMU Agent must have been installed on the VM image (proxmox setting).
    # Then run qemu CLI command to connect to the VM and get the 
    # IP adress given to it via DHCP.

    client = SSHClient()
    username = params['_target']['user'].split('@')
    client.set_missing_host_key_policy(AutoAddPolicy()) # to avoid the usual SSH known_hosts error
    client.connect(hostname=params['_target']['uri'], username=username[0], password=params['_target']['password'])
    cmd_to_execute = 'qm guest cmd ' + post_data['newid'] + ' network-get-interfaces'
    ssh_stdin, ssh_stdout, ssh_stderr = client.exec_command(cmd_to_execute)
    vm_info_str  = ssh_stdout.read().decode() # return a string version of the JSON Payload result
    vm_info_dict = json.loads(vm_info_str) # convert the string Payload to Python Dict 
    ip_address   = vm_info_dict[1]['ip-addresses'][0]['ip-address']
    return ip_address 



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

    # DON'T REMOVE START TO FINISH section, its for debugging
    ### START 
    #out_file = open("inventory_test2.json", "w") 
    #out_file.close() 
    #exit(1)
    #with open('/home/rajesh/proxmox/bolt/bolt_appstack_cloud_work/inventory_test2.json') as f:
    #     params = json.load(f)
    #params['apps_stack_filename'] = '/home/rajesh/proxmox/bolt/bolt_appstack_cloud_work/apps_stack.yaml'
    #### FINISH 

    proxmox = ProxmoxAPI(params['_target']['uri'], user=params['_target']['user'], password= params['_target']['password'], verify_ssl=False)
    #print(proxmox.access.users.get()) # for debug purposes

    # get the apps node from inventory file
    import yaml
    with open(params['apps_stack_filename']) as file:
        apps_stacks_yaml = yaml.safe_load(file)

    # build generated_inventory dict
    # pre-amble: add the targets
    generated_inventory['targets'] = []
    
    #print(apps_stacks_yaml)
    apps = apps_stacks_yaml['apps']
    msg =""
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
                ip_address = get_ip_address(params, post_data)
                msg += " with IP address: " + ip_address
                node_info = {
                    "name" : vm_name,
                    "uri"  : ip_address,
                    "vmid" : post_data['newid'],
                    "plan" : app['plan'],
                    "plan_params": app['plan_params']

                }
                generated_inventory['targets'].append(node_info)
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
            ip_address = get_ip_address(params, post_data)
            msg += " with IP address: " + ip_address
            node_info = {
                    "name" : app['name'],
                    "uri"  : ip_address,
                    "vmid" : post_data['newid'],
                    "plan" : app['plan'],
                    "plan_params": app['plan_params']

                }
            generated_inventory['targets'].append(node_info)
            
    
    # post-amble. add the config section from the apps inventory file
    generated_inventory['config'] = {}
    for key,val in dict.items(apps_stacks_yaml['config']):
        generated_inventory['config'][key] = val
    
# main
urllib3.disable_warnings() # stop https warnings
execute()
print(generated_inventory)
