# -*- coding: utf-8 -*-
# Copyright (C) 2012-2013 Mag. Christian Tanzer All rights reserved
# Glasauergasse 32, A--1130 Wien, Austria. tanzer@swing.co.at
# #*** <License> ************************************************************#
# This module is part of the program FFG.
#
# This module is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This module is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this module. If not, see <http://www.gnu.org/licenses/>.
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
#    ««revision-date»»···
#--

from   __future__  import absolute_import, division, print_function, unicode_literals

from   _TFL                   import TFL
import _TFL.Command

class _Base_Command_ (TFL.Command.Root_Command) :

    nick                  = u"FFG"

    class Config_Dirs (TFL.Command.Root_Command.Config_Dirs) :

        _defaults = ("~/", "$app_dir/../..", "~/httpd_config", "$app_dir/httpd_config")

    # end class Config_Dirs

    class Config (TFL.Command.Root_Command.Config) :

        _default = ".ffg.config"

    # end class Config

# end class _Base_Command_

### __END__ _Base_Command_