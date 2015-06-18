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
#    fixtures
#
# Purpose
#    Create standard objects for new scope
#
# Revision Dates
#    17-Dec-2012 (RS) Creation, move old fixtures.py to _FFW
#    27-May-2013 (CT) Remove trivial `password` values
#    28-Apr-2014 (CT) Add account `aaron@lo-res.org` and group `FFW-admin`
#    01-Sep-2014 (MB) Add account 'mihi@lo-res.org'
#    01-Sep-2014 (MB) Move to FFG
#    18-Jun-2015 (CT) Remove Viennese accounts, add Graz specific accounts
#    ««revision-date»»···
#--

from   __future__  import absolute_import, division
from   __future__  import print_function, unicode_literals

from   _CNDB               import CNDB
import _CNDB._OMP.fixtures

def create_account \
        ( scope, last_name, first_name, email
        , superuser   = False
        , middle_name = None
        , title       = None
        , enabled     = True
        , suspended   = False
        , ** kw
        ) :
    Auth = scope.Auth
    PAP  = scope.PAP
    p    = PAP.Person (last_name, first_name, middle_name, title, ** kw)
    a    = Auth.Account.create_new_account_x \
        ( email
        , enabled     = enabled
        , superuser   = superuser
        , suspended   = suspended
        )
    PAP.Person_has_Account (p, a)
    return a
# end def create_account

def create (scope) :
    CNDB.OMP.fixtures.create (scope)
    Auth = scope.Auth
    ffg  = Auth.Group ("FFG")
    adm  = Auth.Group ("FFG-admin")
    create_account (scope, "List", "Alex", "alex@list.priv.at", True)
    create_account (scope, "Gantner", "Peter", "funkfeuer@nephros.org", True)
    create_account (scope, "Pointner", "Christian", "equinox@ffgraz.net", True)
    create_account (scope, "Schweizer", "Jürgen", "funkfeuer@pirka.at", True)
# end def create

if __name__ == "__main__" :
    from Command import *
    db_url  = sos.environ.get ("DB_url",  "hps://")
    db_name = sos.environ.get ("DB_name", None)
    scope   = command.scope   (db_url, db_name, False)
    TFL.Environment.py_shell  ()
### __END__ fixtures
