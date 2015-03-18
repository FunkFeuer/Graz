# -*- coding: utf-8 -*-
# Copyright (C) 2012-2015 Mag. Christian Tanzer All rights reserved
# Glasauergasse 32, A--1130 Wien, Austria. tanzer@swing.co.at
# #*** <License> ************************************************************#
# This module is part of the program FFG.
#
# This module is licensed under the terms of the BSD 3-Clause License
# <http://www.c-tanzer.at/license/bsd_3c.html>.
# #*** </License> ***********************************************************#
#
#++
# Name
#    _Base_Command_
#
# Purpose
#    Base command for FFG model and deploy commands
#
# Revision Dates
#     3-Jun-2012 (CT) Creation
#    17-Dec-2013 (CT) Add `httpd_config` to `Config_Dirs._defaults`
#    01-Sep-2014 (MB) Moved to FFG
#    18-Mar-2015 (CT) Added documentation for `Config_Dirs._defaults`
#    ««revision-date»»···
#--

from   __future__  import absolute_import, division, print_function, unicode_literals

from   _TFL                   import TFL
import _TFL.Command

class _Base_Command_ (TFL.Command.Root_Command) :

    nick                  = u"FFG"

    class Config (TFL.Command.Root_Command.Config) :

        _default = ".ffg.config"

    # end class Config

    if False : ### enable if you want to override Config_Dirs._defaults
        class Config_Dirs (TFL.Command.Root_Command.Config_Dirs) :
            """Define the directories in which config files with relative names are
               looked for.

               If a config file with a specific name occurs in more than one config
               directory, all occurences are read and the values combined. Values
               read from later config directories override values defined in
               earlier directories.

               For an entry like "$app_dir/httpd_config", `$app_dir` will be
               replaced by the directory where the `deploy.py` or `Command.py` was
               loaded from. Using entries like `~/...` of `$app_dir/...`, allows
               easy relocation of the projects files.
            """

            ### override `_defaults` with the Node-DB Graz specific list of config
            ### directories
            ### e.g.,
            ###     _defaults = ("<config-dir-1>", "<config-dir-2>")

        # end class Config_Dirs

# end class _Base_Command_

### __END__ _Base_Command_
