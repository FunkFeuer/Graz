README for the Funkfeuer/Graz web app
=======================================

:Authors:

    Christian Tanzer
    <tanzer@swing.co.at>

    Ralf Schlatterbeck
    <rsc@runtux.com>

The Funkfeuer/Graz (FFG) web app is an application that serves data about
the network nodes deployed by Funkfeuer Graz.

It uses the `tapyr framework`_ and the `common node database`_ (CNDB).

.. _`tapyr framework`: https://github.com/Tapyr/tapyr
.. _`common node database`: https://github.com/FunkFeuer/common-node-db

System requirements
--------------------

See https://github.com/FunkFeuer/common-node-db#system-requirements

Package Installation for Debian Stable aka Wheezy
--------------------------------------------------

See https://github.com/FunkFeuer/common-node-db#package-installation-for-debian-stable-aka-wheezy

How to install
--------------

See https://github.com/FunkFeuer/common-node-db#how-to-install (replace `Wien`
by `Graz`, `ffw` by `ffg` or whatever)

During the testing phase: Whenever we upgrade the software, the
converter (from the old Graz database to the new one) will be run again.
The following steps will prepare the "passive" deployment version and
run the converter. This is similar to migrating to a new version (see
below) except that we're running the converter instead of migrating the
old version (because usually the Graz database has moved on and we want
the latest version from the latest dump)::

    ### Set correct virtual environment and PYTHONPATH, note that we
    ### need to explicitly set the PYTHONPATH to the passive environment
    $ source PVE/active/bin/activate
    $ export PYTHONPATH=/home/ffg/passive/cndb:/home/ffg/passive/tapyr

    ### Update source code
    $ python passive/www/app/deploy.py update

    ### Byte compile python files
    $ python passive/www/app/deploy.py pycompile

    ### Compile translations
    $ python passive/www/app/deploy.py babel compile

    ### Run the converter with database dump version XXXX
    $ python passive/www/app/convert_graz.py ffgraz_XXXX

    ### Setup app cache
    $ python passive/www/app/deploy.py setup_cache

  ### Switch active and passive branches
  $ python passive/www/app/deploy.py switch
  $ sudo /etc/init.d/apache2 restart

Contact
-------

Christian Tanzer <tanzer@swing.co.at> and
Ralf Schlatterbeck <rsc@runtux.com>
