#!/usr/bin/python
# -*- coding: utf-8 -*-
# #*** <License> ************************************************************#
# This module is part of the program FFG.
#
# This module is licensed under the terms of the BSD 3-Clause License
# <http://www.c-tanzer.at/license/bsd_3c.html>.
# #*** </License> ***********************************************************#

from   __future__             import print_function

from   _TFL.pyk               import pyk

import sys, os
import re
import csv
import uuid

from   datetime               import datetime, date, tzinfo, timedelta
from   rsclib.IP_Address      import IP4_Address
from   rsclib.Phone           import Phone
from   rsclib.sqlparser       import make_naive, SQL_Parser
from   _GTW                   import GTW
from   _TFL                   import TFL
from   _CNDB                  import CNDB
import _CNDB._OMP
from   _GTW._OMP._PAP         import PAP
from   _MOM.import_MOM        import Q

import _TFL.CAO
import Command

class Network (object) :

    def __init__ (self, convert, ip, node, net_id, parent, owner) :
        self.convert  = convert
        self.ip       = ip
        self.node     = node
        self.netids   = {net_id : 1}
        self.parent   = parent
        self.owner    = owner
        self.rescount = 0
        self.res      = {}
        self.network  = None
    # end def __init__

    def join (self, other) :
        assert other.node      == self.node
        assert other.parent    == self.parent
        assert other.owner     == self.owner
        assert other.ip.parent == self.ip.parent
        self.netids.update (other.netids)
        self.ip = self.ip.parent
    # end def join

    def reserve (self, ip) :
        assert ip in self.ip
        assert ip not in self.res
        self.res [ip]  = 1
        self.rescount += 1
        if self.ip.mask < 32 :
            if not self.network :
                self.reserve_network ()
            return self.network
        return self.parent
    # end def reserve

    def reserve_network (self) :
        if self.network :
            return self.network
        # Don't reserve a pool for allocated single ips
        if self.rescount and self.ip.mask == 32 :
            print ("Fully reserved: %s" % self.ip)
            return
        if self.parent :
            assert self.ip in self.parent.net_address
            assert self.ip != self.parent.net_address
            reserver = self.parent.reserve
        else :
            print ("WARN: No parent: new network: %s" % self.ip)
            reserver = self.convert.ffw.IP4_Network
        network = reserver (self.ip, owner = self.owner)
        print ("reserved: %s" % self.ip,)
        comment = {}
        for k in self.netids :
            self.convert.net_by_id [k] = network
            n = self.convert.ff_net_by_id [k]
            if n.comment :
                comment [n.comment] = 1
        if comment :
            network.set_raw (desc = '\n'.join (sorted (comment)))
        if self.node :
            node = self.node
            print (node.name, end = " ")
            if node not in self.convert.node_pools :
                self.convert.node_pools [node] = self.convert.ffw.IP4_Pool \
                    (name = node.name, node = node)
            pool = self.convert.node_pools [node]
            self.convert.ffw.IP4_Network_in_IP4_Pool (network, pool)
        print
        self.network = network
        return network
    # end def reserve_network

# end class Network

class Convert (object) :

        #  54  :  655 # nick == email vorn?
    person_dupes = \
        {  71  :   72
        , 140  :  460
        , 179  :  124
        , 265  :  1039
        , 267  :  322
        , 273  :  272 # probably same unnamed person, almost same nick
        , 276  :  272 # yet another dupe with almost same nick
        , 307  :  306
        , 314  :  311
        , 372  :  380 # same phone *and* password (!) different name (!)
        , 424  :  418
        , 440  :  838
        , 617  :  623
        , 669  : 1001 # same person?
        , 686  :  687
        , 708  :  707
        , 709  :  707
        , 718  :  860
        , 729  :  728
        , 741  :  740
        , 755  :  754
        , 776  :  301
        , 799  :  807
        , 820  :  359
        , 821  :  359
        , 831  :  836
        , 852  :  851
        , 892  :  706
        , 903  :  904
        , 973  :  544
        , 1005 : 1007
        , 1036 : 1014
        }

    person_ignore = dict.fromkeys \
        ((  11
         ,  15
         ,  41
         ,  42
         ,  62
         ,  63
         ,  64
         ,  66
         ,  70
         ,  93
         , 100
         , 106
         , 108
         , 112
         , 118
         , 123
         , 132
         , 136
         , 142
         , 172
         , 174
         , 177
         , 199
         , 209
         , 242
         , 244
         , 245
         , 254
         , 263
         , 266
         , 270
         , 287
         , 313
         , 320
         , 324
         , 338
         , 937
         # Lastname missing:
         ,  34
         ,  69
         , 107
         , 166
         , 168
         , 200
         , 251
         , 260
         , 323
         # Bogus, only initials etc, ignore if no node:
         , 102
         , 103
         , 185
         , 233
         , 299
         , 455
         , 530
         , 845
         , 872
         , 919
         , 955
        ))

    def __init__ (self, cmd, scope, debug = False) :
        self.anonymize = cmd.anonymize
        self.verbose   = cmd.verbose
        self.pers_exception = {}
        try :
            pf = open ('pers.csv', 'r')
            cr = csv.reader (pf, delimiter = ';')
            for line in cr :
                self.pers_exception [int (line [0])] = (line [1], line [2])
        except IOError :
            print ("WARN: Can't read additional person data")

        self.debug = debug
        if len (cmd.argv) > 0 :
            f  = open (cmd.argv [0])
        else :
            f = sys.stdin
        self.scope        = scope
        self.ffw          = self.scope.CNDB
        self.pap          = self.scope.GTW.OMP.PAP
        self.networks     = {}

        self.parser       = SQL_Parser (verbose = False, fix_double_encode = 1)
        self.parser.parse (f)
        self.contents     = self.parser.contents
        self.tables       = self.parser.tables
        self.dev_by_id    = {}
        self.ffw_node     = {}
        self.member_by_id = {}
        self.net_by_id    = {}
        self.nicknames    = {}
        self.nifin_by_id  = {}
        self.ntype_by_id  = {}
        self.node_by_id   = {}
        self.person_by_id = {}
        self.phone_ids    = {}
        self.node_pools   = {}
    # end def __init__

    def create (self) :
        self.fugru = self.pap.Adhoc_Group ("Funker Gruppe")
        if self.anonymize :
            self.fake_persons ()
        else :
            self.create_persons ()
        self.create_nettypes ()
        self.scope.commit ()
        self.create_nodes   ()
        self.scope.commit ()
        self.create_networks ()
        self.scope.commit ()
        self.create_devices ()
        self.scope.commit ()
        self.create_interfaces ()
        self.scope.commit ()
        self.create_dns_aliases ()
        self.scope.commit ()
    # end def create

    def create_devices (self) :
        # ignore snmp_ip and snmp_lastseen (only used by three nodes)
        secondary_nodes = {}
        dt = self.ffw.Net_Device_Type.instance (name = 'Generic', raw = True)
        for d in sorted (self.contents ['node'], key = lambda x : x.id) :
            self.vprint ("INFO: Dev: %s Node: %s" % (d.id, d.location_id))
            node = None
            n = self.node_by_id.get (d.location_id)
            if n :
                if  (  d.person_id
                    and d.person_id != n.person_id
                    and d.person_id in self.person_by_id
                    ) :
                    if (d.person_id, n.id) in secondary_nodes :
                        node = secondary_nodes [(d.person_id, n.id)]
                        self.vprint \
                            ( "INFO: Device (node) %s, (loc) %s: "
                              "existing secondary node for d:%s/n:%s"
                            % (d.id, n.id, d.person_id, n.person_id)
                            )
                    else :
                        self.vprint \
                            ( "INFO: Device (node) %s, (loc) %s: "
                              "manufacturing secondary node for d:%s/n:%s"
                            % (d.id, n.id, d.person_id, n.person_id)
                            )
                        pn   = self.ffw_node.get (n.id)
                        mgr  = self.person_by_id.get (d.person_id)
                        txt  = 'Auto-created node (id: %s) for "%s"' \
                             % (d.location_id, n.name)
                        node = self.ffw.Node \
                            ( name        = '/'.join ((n.name, d.name))
                            , desc        = txt
                            , manager     = mgr
                            , raw         = True
                            , show_in_map = pn.show_in_map
                            , position    = pn.position
                            )
                        secondary_nodes [(d.person_id, n.id)] = node
                else :
                    node = self.ffw_node.get (d.location_id)
                    if not node :
                        print \
                            ( "WARN: Node (location) %s "
                              "for dev (node) %s missing" \
                            % (d.location_id, d.id)
                            )
                        continue
            else :
                mgr  = self.person_by_id.get (d.person_id) or self.graz_admin
                self.vprint \
                    ( "INFO: Manufacturing Node (loc: %s) for dev (node) %s"
                    % (d.location_id, d.id)
                    )
                name = d.name
                exn  = self.ffw.Node.instance (d.name)
                if exn :
                    name = '-'.join ((str (d.location_id), d.name))
                node = self.ffw.Node \
                    ( name        = name
                    , desc        = 'Auto-created node (id: %s)' % d.location_id
                    , show_in_map = True
                    , manager     = mgr
                    , raw         = True
                    )
            dev = self.ffw.Net_Device \
                ( left = dt
                , node = node
                , name = d.name
                , desc = d.comment
                , raw  = True
                )
            self.set_creation (dev, d.time)
            self.dev_by_id [d.id] = dev
            if len (self.scope.uncommitted_changes) > 10 :
                self.scope.commit ()
    # end def create_devices

    def create_dns_aliases (self) :
        for dal in self.contents ['dnsalias'] :
            if dal.ip_id not in self.nifin_by_id :
                print \
                    ( 'WARN: ignoring dns_alias %s "%s" IP not found %s'
                    % (dal.id, dal.name, dal.ip_id)
                    )
                return
            self.ffw.IP4_DNS_Alias \
                (left = self.nifin_by_id [dal.ip_id], name = dal.name)
            if len (self.scope.uncommitted_changes) > 10 :
                self.scope.commit ()
    # end def create_dns_aliases

    def create_interfaces (self) :
        for iface in self.contents ['ip'] :
            if iface.node_id not in self.dev_by_id :
                print \
                    ( "WARN: Ignoring IP %s %s: no device (node) %s"
                    % (iface.id, iface.ip, iface.node_id)
                    )
                continue
            dev = self.dev_by_id [iface.node_id]
            ip  = IP4_Address (iface.ip)
            # Originally in a /32 reserved network
            if ip in self.node_ips :
                nw = self.node_ips [ip]
                net = nw.reserve (ip)
                assert ip in net.net_address
                if iface.net_id not in nw.netids :
                    print \
                        ( "WARN: Referenced wrong network: %s %s"
                        % (iface.net_id, ip)
                        )
            else :
                net = self.net_by_id [iface.net_id]
            nw  = net.reserve (ip, owner = dev.node.owner)
            nif = self.ffw.Wired_Interface (left = dev, name = iface.name)
            nii = self.ffw.Net_Interface_in_IP4_Network \
                (nif, nw, mask_len = 32, name = iface.name)
            self.nifin_by_id [iface.id] = nii
            if len (self.scope.uncommitted_changes) > 10 :
                self.scope.commit ()
        for ip in self.node_ips :
            self.node_ips [ip].reserve_network ()
    # end def create_interfaces

    def create_nettypes (self) :
        """ Network ranges for reservation
        """
        # Create all rfc1918 networks as top-level pools
        for net_ip in '172.16.0.0/12', '10.0.0.0/8', '192.168.0.0/16' :
            ip   = IP4_Address (net_ip)
            nw   = self.ffw.IP4_Network (ip, owner = self.graz_admin)
            pool = self.ffw.IP4_Pool (name = 'RFC 1918 %s' % net_ip)
            self.ffw.IP4_Network_in_IP4_Pool (nw, pool)

        by_mask    = {}
        pool_by_id = {}
        # first group by netmask
        for nw in self.contents ['nettype'] :
            if not nw.comment :
                print ('WARN: Ignoring nettype %s "%s"' % (nw.id, nw.name))
                continue
            pool = pool_by_id [nw.id] = self.ffw.IP4_Pool (name = nw.name)
            if nw.name == 'GRAZ Client Subnet /29' :
                self.ffw.IP4_Pool_permits_Group \
                    (pool, self.fugru, node_quota = 29)
            netmask = None
            try :
                netmask = int (nw.name.split ('/') [-1])
            except ValueError :
                pass
            if netmask :
                pool.set (netmask_interval = (netmask,))
            for net_ip in nw.comment.split (',') :
                ip = IP4_Address (net_ip)
                if ip.mask not in by_mask :
                    by_mask [ip.mask] = []
                by_mask [ip.mask].append ((ip, nw.name, nw.id))
        typ = self.ffw.IP4_Network
        for mask in sorted (by_mask) :
            for ip, name, id in by_mask [mask] :
                if id not in self.ntype_by_id :
                    self.ntype_by_id [id] = []
                r = typ.query \
                    ( Q.net_address.CONTAINS (ip)
                    , ~ Q.electric
                    , sort_key = TFL.Sorted_By ("-net_address.mask_len")
                    ).first ()
                reserver = r.reserve if r else typ
                network  = reserver (ip, owner = self.graz_admin)
                self.ntype_by_id [id].append (network)
                self.ffw.IP4_Network_in_IP4_Pool (network, pool_by_id [id])
                if name :
                    network.set_raw (desc = name)
    # end def create_nettypes

    def create_networks (self) :
        self.node_ips     = {}
        ipdict            = {}
        self.ff_net_by_id = {}
        for net in self.contents ['net'] :
            self.ff_net_by_id [net.id] = net
            parents = self.ntype_by_id.get (net.nettype_id, [])
            node    = self.ffw_node.get (net.location_id)
            ip      = IP4_Address (net.netip, net.netmask)
            if parents and ip == parents [0].net_address :
                self.net_by_id [net.id] = parents [0]
                continue
            if node :
                owner = node.owner
            else :
                print \
                    ( "WARN: Network %s %s Location %s missing"
                    % (net.id, net.netip, net.location_id)
                    )
                owner = self.graz_admin
            parent = None
            for p in parents :
                if ip in p.net_address :
                    parent = p
                    break
            else :
                parent = None
                for ps in pyk.itervalues (self.ntype_by_id) :
                    for p in ps :
                        if ip in p.net_address :
                            parent = p
                            self.vprint \
                                ("Got parent in ntype_by_id: %s" % parent)
                            break
                else :
                    parent = self.ffw.IP4_Network.query \
                        ( Q.net_address.CONTAINS (ip)
                        , ~ Q.electric
                        , sort_key = TFL.Sorted_By ("-net_address.mask_len")
                        ).first ()
                    if parent :
                        self.vprint ("Got parent by network query: %s" % parent)
            ipdict [ip] = Network (self, ip, node, net.id, parent, owner)

        mask = 32
        while mask and ipdict :
            # Dict is modified during iteration, use keys ()
            for ip in ipdict.keys () :
                # already found via sibling or network still too big
                if ip.mask < mask or ip not in ipdict :
                    continue
                assert ip.mask == mask
                nw = ipdict [ip]
                sib = next \
                    ( k for k in ip.parent.subnets (ip.mask)
                        if  ip.is_sibling (k)
                    )
                # Sibling has same node? -> join to bigger net
                # Only join networks that *have* a node
                if  (   sib in ipdict
                    and nw.node
                    and ipdict [sib].node == nw.node
                    ) :
                    nw.join (ipdict [sib])
                    del ipdict [ip]
                    del ipdict [sib]
                    ipdict [ip.parent] = nw
                else :
                    del ipdict [ip]
                    if nw.node and nw.ip.mask >= 24 :
                        # Don't reserve now, if allocated we don't want a pool
                        for i in nw.ip.subnets (32) :
                            self.node_ips [i] = nw
                    else :
                        nw.reserve_network ()
            if len (self.scope.uncommitted_changes) > 10 :
                self.scope.commit ()
            mask -= 1
    # end def create_networks

    def create_nodes (self) :
        x_start = 4080
        y_start = 4806
        x_lon   = 15.43844103813
        y_lat   = 47.07177327969
        dx_lon  = 50675.5176
        dy_lat  = 75505.521
        for n in sorted (self.contents ['location'], key = lambda x : x.id) :
            self.node_by_id [n.id] = n
            person_id = self.person_dupes.get (n.person_id, n.person_id)
            if person_id != 0 and person_id not in self.person_by_id :
                # should not happen now
                print ("WARN: Location %s owner %s missing" % (n.id, person_id))
                continue
            if person_id == 0 :
                person = self.graz_admin
            else :
                person = self.person_by_id [person_id]
            lat = lon = None
            if n.pixel_x is not None and n.pixel_y is not None :
                lon = "%f" % (x_lon + (n.pixel_x - x_start) / dx_lon)
                lat = "%f" % (y_lat + (n.pixel_y - y_start) / dy_lat)

            node = self.ffw.Node \
                ( name        = n.name
                , desc        = n.comment.strip () or None
                , show_in_map = not n.hidden
                , manager     = person
                , position    = dict (lat = lat, lon = lon)
                , raw         = True
                )
            self.ffw_node [n.id] = node
            self.set_creation (node, n.time)
            if n.street :
                s = ' '.join (x for x in (n.street, n.streetnr) if x)
                adr = self.pap.Address.instance_or_new \
                    ( street  = s
                    , zip     = '8010'
                    , city    = 'Graz'
                    , country = 'Austria'
                    , raw     = True
                    )
                node.set (address = adr)
            if n.gallery_link :
                MOM = self.scope.MOM
                abs = 'http://gallery.funkfeuer.at/v/Graz/Knoten/%s/'
                if n.gallery_link.startswith ('http') :
                    abs = "%s"
                url = MOM.Document \
                    (node, url = abs % n.gallery_link, type = 'Gallery')
            if len (self.scope.uncommitted_changes) > 10 :
                self.scope.commit ()
    # end def create_nodes

    def fake_persons (self) :
        self.graz_admin = self.pap.Person \
            ( first_name = 'Graz'
            , last_name  = 'Admin'
            , raw        = True
            )
        mail  = 'admin@graz.funkfeuer.at'
        email = self.pap.Email (address = mail)
        self.pap.Person_has_Email (self.graz_admin, email)
        auth = self.scope.Auth.Account.create_new_account_x \
            ( mail
            , enabled   = True
            , suspended = True
            , password  = uuid.uuid4 ().hex
            )
        self.pap.Person_has_Account (self.graz_admin, auth)
        for m in sorted (self.contents ['person'], key = lambda x : x.id) :
            self.person_by_id [m.id] = self.graz_admin
    # end def fake_persons

    def create_persons (self) :
        for m in sorted (self.contents ['person'], key = lambda x : x.id) :
            #print ("%s: %r %r" % (m.id, m.firstname, m.lastname))
            if m.id in self.person_ignore :
                print ("WARN: Ignoring anonymous without location: %s" % m.id)
                continue
            if m.id in self.pers_exception :
                pe = self.pers_exception [m.id]
                fn, ln = (pyk.decoded (x, 'utf-8') for x in pe)
            else :
                fn = m.firstname.strip ()
                ln = m.lastname.strip ()
            self.member_by_id [m.id] = m
            if m.id in self.person_dupes :
                print ("WARN: Duplicate person: %s" % m.id)
                continue
            if not fn or not ln :
                print \
                    ( "WARN: name missing: %s (%r/%r)"
                    % (m.id, m.firstname, m.lastname)
                    , file = sys.stderr
                    )
                if not fn and not ln :
                    if m.nick :
                        fn = m.nick
                    else :
                        fn = m.email.split ('@') [0]
                fn = fn or '?'
                ln = ln or '?'
            self.vprint ("Person: %s %r/%r" % (m.id, fn, ln))
            person = self.pap.Person \
                ( first_name = fn
                , last_name  = ln
                , raw        = True
                )
            self.pap.Person_in_Group (person, self.fugru)
            self.person_by_id [m.id] = person
            if m.nick :
                self.try_insert_nick (m.nick, m.id, person)
            if m.email and m.email != '-' :
                mail  = m.email.replace ('[at]', '@')
                try :
                    email = self.pap.Email (address = mail)
                    self.pap.Person_has_Email (person, email)
                    if m.email == 'admin@graz.funkfeuer.at' :
                        g = self.pap.Adhoc_Group ('Admin Group Graz')
                        self.pap.Person_in_Group (person, g)
                        self.graz_admin = g
                    auth = self.scope.Auth.Account.create_new_account_x \
                        ( mail
                        , enabled   = True
                        , suspended = True
                        , password  = uuid.uuid4 ().hex
                        )
                    self.pap.Person_has_Account (person, auth)
                except Exception as exc :
                    print ("WARN: %s" % exc)
            if m.tel :
                self.try_insert_phone (m.tel, m.id, person)
            if len (self.scope.uncommitted_changes) > 10 :
                self.scope.commit ()
        # get data from dupes
        for d_id, m_id in pyk.iteritems (self.person_dupes) :
            # older version of db or dupe removed:
            if d_id not in self.member_by_id or m_id not in self.person_by_id :
                continue
            d = self.member_by_id [d_id]
            m = self.member_by_id [m_id]
            person = self.person_by_id [m_id]
            if d.email :
                email = self.pap.Email (address = d.email)
                self.pap.Person_has_Email (person, email)
            if d.nick :
                self.try_insert_nick (d.nick, m_id, person)
            if d.tel :
                self.try_insert_phone (d.tel, m_id, person)
            if len (self.scope.uncommitted_changes) > 10 :
                self.scope.commit ()
    # end def create_persons

    def set_creation (self, obj, create_time) :
        if not create_time :
            return
        if not isinstance (create_time, datetime) :
            create_time = datetime (* create_time.timetuple () [:3])
        create_time = make_naive (create_time)
        self.scope.ems.convert_creation_change (obj.pid, c_time = create_time)
    # end def set_creation

    def try_insert_phone (self, tel, id, person) :
        if tel.startswith ('06-') :
            print ("WARN: Ignoring invalid phone number: %s" % tel)
            return
        if tel.startswith ('+430659') :
            tel = '+43650' + tel [6:]
        p = Phone (tel, city = "Graz")
        if p :
            k = str (p)
            t = self.pap.Phone.instance (*p)
            if t :
                eid = self.phone_ids [k]
                prs = self.person_by_id [eid]
                if eid != id :
                    print \
                        ( "WARN: %s/%s %s/%s: Duplicate Phone: %s"
                        % (eid, prs.pid, id, person.pid, tel)
                        )
            else :
                self.phone_ids [k] = id
                phone = self.pap.Phone (*p)
                self.pap.Person_has_Phone (person, phone)
    # end def try_insert_phone

    def try_insert_nick (self, nick, id, person) :
        lnick = nick.lower ()
        if lnick in self.nicknames :
            eid = self.nicknames [lnick]
            prs = self.person_by_id [eid]
            if eid != id :
                print \
                    ( "WARN: %s/%s %s/%s Duplicate Nickname: %s"
                    % (eid, prs.pid, id, person.pid, nick)
                    )
        else :
            n = self.pap.Nickname (nick, raw = True)
            self.pap.Person_has_Nickname (person, n)
            self.nicknames [lnick] = id
    # end def try_insert_nick

    def vprint (self, * args) :
        if self.verbose :
            print (* args)
    # end def vprint

# end def Convert


def _main (cmd) :
    scope = Command.scope (cmd)
    if cmd.Break :
        TFL.Environment.py_shell ()
    c = Convert (cmd, scope)
    #c.dump ()
    c.create ()
    scope.commit ()
    scope.ems.compact ()
    scope.destroy ()
# end def _main

_Command = TFL.CAO.Cmd \
    ( handler         = _main
    , args            =
        ( "file:S?PG database dumpfile to convert"
        ,
        )
    , opts            =
        ( "verbose:B"
        , "anonymize:B"
        , "create:B"
        ) + Command.opts
    , min_args        = 1
    , defaults        = Command.command.defaults
    )

if __name__ == "__main__" :
    _Command ()
### __END__ cnml_import
