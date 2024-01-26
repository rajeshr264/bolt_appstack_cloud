#!/usr/bin/env python3
import boto3
from proxmoxer import ProxmoxAPI
import json
import socket 
import os
import sys
import time

def remove_dns_from_route53(fqdn_name):
    """ """
    # AWS 
    # Retrieve AWS credentials from the environment
    aws_access_key_id = os.environ.get('AWS_ACCESS_KEY_ID')
    aws_secret_access_key = os.environ.get('AWS_SECRET_ACCESS_KEY')
    aws_region_name = os.environ.get('AWS_REGION')
    hosted_zone_id = os.environ.get('ROUTE53_HOSTED_ZONE_ID')

    if aws_secret_access_key == None or aws_secret_access_key == None or aws_region_name == None or hosted_zone_id == None  :
        print("Error: Missing AWS Credentials environment variables")
        exit(1)

    fqdn = fqdn_name.split('.') 
    domain_name = '.'.join(fqdn[-2:])

    # Create a Route 53 client
    route53_client = boto3.client('route53', aws_access_key_id=aws_access_key_id, aws_secret_access_key=aws_secret_access_key, region_name=aws_region_name)

    # Replace with the record details you want to add
    record_name = fqdn[0]
    record_type = 'A'
    ttl = 8600

    ip_address = socket.gethostbyname(fqdn_name)
    # Create the record set
    change_batch = {
        'Changes': [
            {
                'Action': 'DELETE',
                'ResourceRecordSet': {
                    'Name': f'{record_name}.{domain_name}',
                    'Type': record_type,
                    'TTL': ttl,
                    'ResourceRecords': [
                        {
                            'Value': ip_address
                        }
                    ]
                }
            }
        ]
    }
    # Update the record set
    response = route53_client.change_resource_record_sets( HostedZoneId=hosted_zone_id, ChangeBatch=change_batch )
    if response['ResponseMetadata']['HTTPStatusCode'] != 200:
         print("Warning: Could not delete record from Route53")

def delete_vm_from_proxmox():
    """ """

    params = json.load(sys.stdin)
    #with open('/home/rajesh/proxmox/bolt/bolt_appstack_cloud_work/to_delete_inventory.json') as f:
    #        params = json.load(f)
    #print(params)

    proxmox = ProxmoxAPI(params['_target']['uri'], user=params['_target']['user'], password= params['_target']['password'], verify_ssl=False)
    #print(proxmox.access.users.get()) # for Proxmox API debug purposes
    
    # we need to find the VMID assigned to the VM, from Proxmox
    proxmox_node = proxmox.nodes(params['_target']['uri'].split('.')[0])  
    vms_info = proxmox_node.qemu().get()
    for vm in vms_info:
        if params['vm_name'] in vm['name']:
            print("Deleting " + vm['name'] + " with vmid " + str(vm['vmid']))
            # Proxmox requires VM to be in 'stopped' state before delete it
            proxmox_node.qemu(vm['vmid']).status.stop.post()
            while True:
                # Get VM status
                vm_status = proxmox_node.qemu(vm['vmid']).status.current().get()
                # Check if the VM is stopped/running
                if vm_status.get('lock') == None and vm_status.get('status') == "stopped":
                    break 
                #  wait for a few seconds before checking again
                time.sleep(4)
            # now that VM is in 'stopped' state, you can delete it. 
            proxmox_node.qemu(vm['vmid']).delete()
            remove_dns_from_route53(vm['name'])

# main
delete_vm_from_proxmox()
