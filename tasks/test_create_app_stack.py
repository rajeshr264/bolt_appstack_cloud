#!/usr/bin/env python3
import json
import sys

generated_inventory = [
        {
          "name": "puppetenterprise.harshamlab.site",
          "uri": "192.168.1.189",
          "vmid": "100",
          "plan": "bolt_appstack_cloud::pe_install",
          "plan_params": "puppetenterprise_params.json"
        },
        {
          "name": "linux-0.harshamlab.site",
          "uri": "192.168.1.190",
          "vmid": "101",
          "plan": "bolt_appstack_cloud::baseline_linux",
          "plan_params": "baseline_linux_params.json"
        },
        {
          "config": {
            "ssh": {
              "user": "serveradmin",
              "private-key": "~/.ssh/automation",
              "native-ssh": "true",
              "run-as": "root"
            }
          }
        }
      ] 
json.dump({'vms': generated_inventory},sys.stdout)

# Returned result:
# [
#   {
#     "target": "pve.harshamlab.site",
#     "action": "task",
#     "object": "bolt_appstack_cloud::create_app_stack",
#     "status": "success",
#     "value": {
#       "vms": [
#         {
#           "name": "puppetenterprise.harshamlab.site",
#           "uri": "192.168.1.174",
#           "vmid": "100",
#           "plan": "bolt_appstack_cloud::pe_install",
#           "plan_params": "puppetenterprise_params.json"
#         },
#         {
#           "name": "linux-0.harshamlab.site",
#           "uri": "192.168.1.175",
#           "vmid": "101",
#           "plan": "bolt_appstack_cloud::baseline_linux",
#           "plan_params": "baseline_linux_params.json"
#         }
#       ]
#     }
#   }
# ]