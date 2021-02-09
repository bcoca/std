#!/usr/bin/env python

import os
import sys

# if you dont have ansible, how are you using collections??
from ansible import constants as C


try:
    C.COLLECTIONS_SCAN_SYS_PATH
    exit("newer Ansible, use: ansible-galaxy collections list")
except AttributeError:
    pass

where = C.COLLECTIONS_PATHS
if len(sys.argv) != 2:
    exit("This script requires a single collection name as an argument.")

what = sys.argv[1]

try:
    ns, coll = what.split('.',1)
except ValueError:
    exit("Invalid collection name supplied: %s" % what)

for path in where:
    collpath = os.path.join(path, 'ansible_collections', ns, coll)
    if os.path.exists(collpath):
        mpath= os.path.join(collpath, 'MANIFEST.json')
        if not os.path.exists(mpath):
            exit("Found collection at '%s' but missing MANIFEST.json, cannot get info." % collpath)

        with open(mpath, 'r') as f:
            print(f.read())
        break
else:
    exit("Collection '%s' not found in '%s'" % (what, where))
