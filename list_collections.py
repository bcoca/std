#!/usr/bin/env python

import os
import sys
import warnings

# if you dont have ansible, how are you using collections??
from ansible import constants as C

try:
    C.COLLECTIONS_SCAN_SYS_PATH
    exit("newer Ansible, use: ansible-galaxy collections list")
except AttributeError:
    pass

where = C.COLLECTIONS_PATHS

found = {}

for path in where:
    collpath = os.path.join(path, 'ansible_collections')
    if os.path.exists(collpath):
        for ns in os.listdir(collpath):
            nsp = os.path.join(collpath, ns)
            if os.path.isdir(nsp):
                for collection in os.listdir(nsp):
                    collp = os.path.join(nsp, collection)
                    if os.path.isdir(collp):
                        info = {'path': collp}
                        cname = '.'.join([ns, collection])
                        if cname in found:
                            warnings.warn("Skipping duplicate %s in %s" % (cname, collp))
                        found[cname] = info

for k in found.keys():
    print(k, found[k]['path'])
