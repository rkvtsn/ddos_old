#!/usr/bin/python
# -*- coding: utf-8 -*-
import sqlite3
import sys, os, subprocess

import config

if not os.getuid() == 0:
    print "You must be root to reinstall firewall"
    sys.exit(2)

sql_query_create = '''CREATE TABLE rules (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  rule_str TEXT NOT NULL,
  life_time TIMESTAMP NOT NULL
);'''

sql_query_delete = '''DROP TABLE IF EXISTS rules'''

if __name__ == "__main__":

    if subprocess.call("iptables-restore < " + config.backup_path, shell=True) != 0:
        print "Somthing wrong with iptables-restore. Please make sure you have install 'iptables-restore' and then try again."
        sys.exit()
    
    conn = sqlite3.connect(config.db_path)
    c = conn.cursor()

    c.execute(sql_query_delete)
    c.execute(sql_query_create)

    conn.commit()

    print "Restored."