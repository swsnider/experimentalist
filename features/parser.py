'''Config file parser'''

import json

from features import config

def parse_config(conf, world):
    conf = json.loads(conf)
    config = {}
    for name, stanza in conf:
        config[name] = config.Feature(name, world, stanza)
    return config
