##########################################################################
#
# pgAdmin 4 - PostgreSQL Tools
#
# Copyright (C) 2013 - 2021, The pgAdmin Development Team
# This software is released under the PostgreSQL Licence
#
##########################################################################

import os
import sys
import json
import config

from flask import render_template
from flask_babelex import gettext as _
from pgadmin.utils.preferences import Preferences
from werkzeug.exceptions import InternalServerError
from pgadmin.utils.constants import BINARY_PATHS
from pgadmin.utils import set_default_binary_path


class ServerType(object):
    """
    Server Type

    Create an instance of this class to define new type of the server support,
    In order to define new type of instance, you may want to override this
    class with overriden function - instanceOf for type checking for
    identification based on the version.
    """
    registry = dict()
    UTILITY_PATH_LABEL = _("PostgreSQL Binary Path")
    UTILITY_PATH_HELP = _(
        "Path to the directory containing the PostgreSQL utility programs"
        " (pg_dump, pg_restore etc)."
    )

    def __init__(self, server_type, description, priority):
        self.stype = server_type
        self.desc = description
        self.spriority = priority
        self.utility_path = None

        assert (server_type not in ServerType.registry)
        ServerType.registry[server_type] = self

    @property
    def icon(self):
        return "%s.svg" % self.stype

    @property
    def server_type(self):
        return self.stype

    @property
    def description(self):
        return self.desc

    @classmethod
    def register_preferences(cls):
        paths = Preferences('paths', _('Paths'))
        bin_paths = BINARY_PATHS

        for key in cls.registry:
            st = cls.registry[key]

            default_bin_path = config.DEFAULT_BINARY_PATHS.get(key, "")
            if default_bin_path != "":
                set_default_binary_path(default_bin_path, bin_paths, key)
            if key == 'pg':
                st.utility_path = paths.register(
                    'bin_paths', 'pg_bin_dir',
                    _("PostgreSQL Binary Path"), 'selectFile',
                    json.dumps(bin_paths['pg_bin_paths']),
                    category_label=_('Binary paths')
                )
            elif key == 'ppas':
                st.utility_path = paths.register(
                    'bin_paths', 'ppas_bin_dir',
                    _("EDB Advanced Server Binary Path"), 'selectFile',
                    json.dumps(bin_paths['as_bin_paths']),
                    category_label=_('Binary paths')
                )

    @property
    def priority(self):
        return self.spriority

    def __str__(self):
        return _("Type: {0}, Description: {1}, Priority: {2}").format(
            self.stype, self.desc, self.spriority
        )

    def instance_of(self, version):
        return True

    @property
    def csssnippets(self):
        """
        Returns a snippet of css to include in the page
        """
        return [
            render_template(
                "css/server_type.css",
                server_type=self.stype,
                icon=self.icon
            )
        ]

    @classmethod
    def types(cls):
        return sorted(
            ServerType.registry.values(),
            key=lambda x: x.priority,
            reverse=True
        )

    def utility(self, operation, sversion):
        res = None

        if operation == 'backup':
            res = 'pg_dump'
        elif operation == 'backup_server':
            res = 'pg_dumpall'
        elif operation == 'restore':
            res = 'pg_restore'
        elif operation == 'sql':
            res = 'psql'
        else:
            raise InternalServerError(
                _("Could not find the utility for the operation '%s'").format(
                    operation
                )
            )

        bin_path = self.get_utility_path(sversion)
        if bin_path is None:
            return None

        if "$DIR" in bin_path:
            # When running as an WSGI application, we will not find the
            # '__file__' attribute for the '__main__' module.
            main_module_file = getattr(
                sys.modules['__main__'], '__file__', None
            )

            if main_module_file is not None:
                bin_path = bin_path.replace(
                    "$DIR", os.path.dirname(main_module_file)
                )

        return os.path.abspath(os.path.join(
            bin_path,
            (res if os.name != 'nt' else (res + '.exe'))
        ))

    def get_utility_path(self, sverison):
        """
        This function is used to get the utility path set by the user in
        preferences for the specific server version, if not set then check
        for any default path is set.
        """
        default_path = None
        bin_path_json = json.loads(self.utility_path.get())
        # iterate through all the path and return appropriate value
        for bin_path in bin_path_json:
            if int(bin_path['version']) <= sverison < \
                int(bin_path['next_major_version']) and \
                    bin_path['binaryPath'] is not None:
                return bin_path['binaryPath']

            if bin_path['isDefault']:
                default_path = bin_path['binaryPath']

        return default_path


# Default Server Type
ServerType('pg', _("PostgreSQL"), -1)
