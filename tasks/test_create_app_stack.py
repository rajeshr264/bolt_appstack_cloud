#!/usr/bin/env python3
import json
import sys

generated_inventory = []

node = {
    "name" : "puppetenterprise.harshamlab.site",
    "ip_address": "192.168.1.152",
    "plan" : "peadm::install",
    "plan_params": "puppetenterprise_params.json"
}

generated_inventory.append(node)
json.dump({'values': list(generated_inventory)},sys.stdout)
