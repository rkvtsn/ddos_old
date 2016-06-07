#!/usr/bin/python
# -*- coding: utf-8 -*-
from os import path

config = None

with open("../config.json") as config_file:
    config = json.load(config_file)


dir = config['firewall']['dir']
db_name = config['firewall']['db_name']
backup_name = config['firewall']['backup_name']

db_path = path.join(dir, db_name)
backup_path = path.join(dir, backup_name)

timeout = config['firewall']['timeout']