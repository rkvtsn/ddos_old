from os import path

dir = "firewall"
db_name = "rules.sqlite"
backup_name = "bak.iptables"

db_path = path.join(dir, db_name)
backup_path = path.join(dir, backup_name)

# timeout for Firewall.Warden seconds
timeout = 60 * 1