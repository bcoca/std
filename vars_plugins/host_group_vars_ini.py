#

from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

DOCUMENTATION = '''
    name: host_group_vars_ini
    short_description: Use ini files in group_vars and host_vars
    description:
        - Loads ini files as vars into corresponding groups/hosts in group_vars/ and host_vars/ directories.
        - Files are restricted by extension to .ini
        - Hidden (starting with '.') and backup (ending with '~') files and directories are ignored.
        - Only applies to inventory sources that are existing paths.
    options:
      on_error:
        description: what to do when encountering an error while parsing files
        choices: ['fatal', 'warn', 'ignore']
        type: str
        default: 'fatal'
        ini:
          - key: on_error
            section: vars_host_group_vars_ini
        env:
          - name: ANSIBLE_VARS_HOST_GROUP_VARS_INI_ON_ERROR
      stage:
        ini:
          - key: stage
            section: vars_host_group_vars_ini
        env:
          - name: ANSIBLE_VARS_PLUGIN_STAGE
    extends_documentation_fragment:
      - vars_plugin_staging
'''

import os
from ansible.errors import AnsibleParserError
from ansible.module_utils._text import to_bytes, to_native, to_text
from ansible.plugins.vars import BaseVarsPlugin
from ansible.inventory.host import Host
from ansible.inventory.group import Group
from ansible.module_utils.six.moves import configparser, StringIO
from ansible.utils.vars import combine_vars

FOUND = {}


class VarsModule(BaseVarsPlugin):

    REQUIRES_WHITELIST = True

    def _error(self, msg):

        do = self.get_optoin('on_error')
        if do == 'fatal':
            raise AnsibleParserError(msg)
        elif do == 'warn':
            self._display.warning(msg)

    def _get_files(self, loader, entity, subdir, cache):

        found_files = []
        # load vars
        b_opath = os.path.realpath(to_bytes(os.path.join(self._basedir, subdir)))
        opath = to_text(b_opath)
        key = '%s.%s' % (entity.name, opath)
        if cache and key in FOUND:
            found_files = FOUND[key]
        else:
            # no need to do much if path does not exist for basedir
            if os.path.exists(b_opath):
                if os.path.isdir(b_opath):
                    self._display.debug("\tprocessing dir %s" % opath)
                    found_files = loader.find_vars_files(opath, entity.name, extensions=['.ini'])
                    FOUND[key] = found_files
                else:
                    self._display.warning("Found %s that is not a directory, skipping: %s" % (subdir, opath))

        return found_files

    def _get_files_data(self, loader, ip, files):

        data = {}
        for found in files:
            contents, show_data = loader._get_file_contents(found)
            try:
                ip.readfp(StringIO(contents))
            except configparser.Error as e:
                self._error("error loading '%s' as ini, check content: %s " % (found, to_native(e)))

            new_data = {}
            for sect in ip.sections():
                if sect not in new_data:
                    new_data[sect] = {}
                for opt in ip.options(sect):
                    val = ip.get(sect, opt)
                    new_data[sect][opt] = val

            if new_data:  # ignore empty files
                data = combine_vars(data, new_data)

        return data

    def get_vars(self, loader, path, entities, cache=True):
        ''' parses the inventory file '''

        if not isinstance(entities, list):
            entities = [entities]

        super(VarsModule, self).get_vars(loader, path, entities)

        data = {}
        ini_parser = configparser.ConfigParser()
        for entity in entities:
            if isinstance(entity, Host):
                subdir = 'host_vars'
            elif isinstance(entity, Group):
                subdir = 'group_vars'
            else:
                raise AnsibleParserError("Supplied entity must be Host or Group, got %s instead" % (type(entity)))

            # avoid 'chroot' type inventory hostnames /path/to/chroot
            if not entity.name.startswith(os.path.sep):
                try:
                    found_files = self._get_files(loader, entity, subdir, cache)
                    new_data = self._get_files_data(loader, ini_parser, found_files)
                    if new_data:  # ignore empty data
                        data = combine_vars(data, new_data)

                except Exception as e:
                    raise AnsibleParserError(to_native(e))

        return data
