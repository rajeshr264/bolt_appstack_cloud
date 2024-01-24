#!/usr/bin/env python3

import json
import urllib3
import time 
import yaml
import os
import sys
import boto3
from paramiko import SSHClient, AutoAddPolicy

# ARRAY to host all the machine info
generated_inventory = []

def add_route53_dns_record(fqdn_name, ip_address):

    # Retrieve AWS credentials from the environment
    aws_access_key_id = os.environ.get('AWS_ACCESS_KEY_ID')
    aws_secret_access_key = os.environ.get('AWS_SECRET_ACCESS_KEY')
    aws_region_name = os.environ.get('AWS_REGION')
    route53_host_zone_id = os.environ.get('ROUTE53_HOSTED_ZONE_ID')

    if aws_secret_access_key == None or aws_secret_access_key == None or aws_region_name == None or route53_host_zone_id == None  :
        print("Error: Missing AWS Credentials environment variables")
        exit(1)


    # params = {
    #     'fqdn' :  "puppetenterprise.harshamlab.site",
    #     'ip_address': '192.168.1.125',
    #  
    # }

    fqdn = fqdn_name.split('.')

    # Replace with your hosted zone ID and domain
    hosted_zone_id = route53_host_zone_id
    domain_name = '.'.join(fqdn[-2:])

    # Create a Route 53 client
    route53_client = boto3.client('route53', aws_access_key_id=aws_access_key_id, aws_secret_access_key=aws_secret_access_key, region_name=aws_region_name)

    # Replace with the record details you want to add
    record_name = fqdn[0]
    record_type = 'A'
    ttl = 8600
    record_value = ip_address

    # Create the record set
    change_batch = {
        'Changes': [
            {
                'Action': 'UPSERT',
                'ResourceRecordSet': {
                    'Name': f'{record_name}.{domain_name}',
                    'Type': record_type,
                    'TTL': ttl,
                    'ResourceRecords': [
                        {
                            'Value': record_value
                        }
                    ]
                }
            }
        ]
    }

    # Update the record set
    response = route53_client.change_resource_record_sets( HostedZoneId=hosted_zone_id, ChangeBatch=change_batch )

    #print(f"Change submitted with status code: {response['ResponseMetadata']['HTTPStatusCode']}")


def generate_inventory_file(inventory_filename, apps_stacks):
    """Generate a Bolt compliant Inventory file"""

    inventory_file = open(inventory_filename,'w')   
    inventory_file.write("targets: \n")
    for node in generated_inventory:
        inventory_file.write("   - name: " + node['name'] + "\n")
        inventory_file.write("     uri: " + node['uri'] + "\n")
    
    inventory_file.write("config: \n  ")
    inventory_file.close()
    # add the 'config' section
    config_section = apps_stacks['config']
    with open(inventory_filename,'a') as inventory_file:
        yaml.dump(config_section, inventory_file, default_style=False, default_flow_style=False, indent=4)

    # add the config section as last part of generated_inventory
    config_hash = {'config' : apps_stacks['config']}
    generated_inventory.append(config_hash)

def run_dummy_ssh_connect(ip_address):
    """Run a dummy ssh connect"""
    client = SSHClient()
    username = 'serveradmin'
    client.set_missing_host_key_policy(AutoAddPolicy()) # to avoid the usual SSH known_hosts error
    try:
        client.connect(hostname=ip_address, username=username, password='dummy')
    except Exception as e:
        pass

    return

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
    # with open('/home/rajesh/proxmox/bolt/bolt_appstack_cloud_work/inventory_test2.json') as f:
    #        params = json.load(f)
    # params['apps_stack_filename'] = '/home/rajesh/proxmox/bolt/bolt_appstack_cloud_work/apps_stack.yaml'
    #### FINISH 

    proxmox = ProxmoxAPI(params['_target']['uri'], user=params['_target']['user'], password= params['_target']['password'], verify_ssl=False)
    #print(proxmox.access.users.get()) # for Proxmox API debug purposes

    # get the apps node from inventory file
    with open(params['apps_stack_filename']) as file:
        apps_stacks = yaml.safe_load(file)   
    #print(apps_stacks_yaml)

    # go thru the apps_stacks
    apps = apps_stacks['apps']
    msg =""
    proxmox_node = proxmox.nodes(params['_target']['name'].split('.')[0])  
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
                # add DNS entry 
                add_route53_dns_record(vm_name, ip_address)
                msg += " with IP address: " + ip_address
                node_info = {
                    "name" : vm_name,
                    "uri"  : ip_address,
                    "vmid" : post_data['newid'],
                    "plan" : app['plan'],
                    "plan_params": app['plan_params']
                }
                # hack: ssh connection doesn't work first time you connect, hence run a dummy command
                run_dummy_ssh_connect(ip_address)
                # build generated_inventory array
                generated_inventory.append(node_info)
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
            add_route53_dns_record(app['name'], ip_address)
            msg += " with IP address: " + ip_address
            node_info = {
                    "name" : app['name'],
                    "uri"  : ip_address,
                    "vmid" : post_data['newid'],
                    "plan" : app['plan'],
                    "plan_params": app['plan_params']

            }
            # hack: ssh connection doesn't work first time you connect, hence run a dummy command
            run_dummy_ssh_connect(ip_address)  
            # build generated_inventory array
            generated_inventory.append(node_info)
    
    # generate the inventory file
    generate_inventory_file(params['generated_inventory_filename'], apps_stacks)
        

# main
urllib3.disable_warnings() # stop https-related warnings from Python HTTP library
execute()
json.dump({'vms': generated_inventory},sys.stdout)
