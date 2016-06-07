#!/usr/bin/python
# -*- coding: utf-8 -*-
from os import path

dir = "dat"
db_name = "rules.sqlite"
backup_name = "bak.iptables"

db_path = path.join(dir, db_name)
backup_path = path.join(dir, backup_name)

# timeout for Firewall.Warden seconds
timeout = 1*60