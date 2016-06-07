#
import json

config = None

with open("../config.json") as config_file:
    config = json.load(config_file)