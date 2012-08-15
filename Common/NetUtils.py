"""
Networking related utilities and common code

Copyright 2012 Red Hat, Inc.
Licensed under the GNU General Public License, version 2 as
published by the Free Software Foundation; see COPYING for details.
"""

__author__ = """
rpazdera@redhat.com (Radek Pazdera)
"""

import logging
import os
import re
import socket
import subprocess

def normalize_hwaddr(hwaddr):
    return hwaddr.upper().rstrip("\n")

def scan_netdevs():
    sys_dir = "/sys/class/net"
    scan = []
    for root, dirs, files in os.walk(sys_dir):
        if "lo" in dirs:
            dirs.remove("lo")
        for d in dirs:
            dev_path = os.path.join(sys_dir, d)
            addr_path = os.path.join(dev_path, "address")
            if not os.path.isfile(addr_path):
                continue
            handle = open(addr_path, "rb")
            addr = handle.read()
            handle.close()
            addr = normalize_hwaddr(addr)
            scan.append({"name": d, "hwaddr": addr})
    return scan

def get_corespond_local_ip(query_ip):
    """
    Get ip address in local system which can communicate with query_ip.

    @param query_ip: IP of client which want communicate with autotest machine.
    @return: IP address which can communicate with query_ip
    """
    query_ip = socket.gethostbyname(query_ip)
    ip = subprocess.Popen("ip route get %s" % (query_ip),
                          shell=True, stdout=subprocess.PIPE,
                          stderr=subprocess.STDOUT)
    ip = ip.communicate()[0]
    ip = re.search(r"src ([0-9.]*)",ip)
    if ip is None:
        return ip
    return ip.group(1)

class AddressPool:
    def __init__(self, start, end):
        self._next = self._addr_to_byte_string(start)
        self._final = self._addr_to_byte_string(end)

    def _inc_byte_string(self, byte_string):
        if len(byte_string):
            byte_string[-1] += 1
            if byte_string[-1] > 255:
                del byte_string[-1]
                self._inc_byte_string(byte_string)
                byte_string.append(0)

    def _addr_to_byte_string(self, addr):
        pass

    def _byte_string_to_addr(self, byte_string):
        pass

    def get_addr(self):
        if self._next > self._final:
            msg = "Pool exhausted, no free addresses available"
            raise Exception(msg)

        addr_str = self._byte_string_to_addr(self._next)
        self._inc_byte_string(self._next)

        return addr_str

class MacPool(AddressPool):
    def _addr_to_byte_string(self, addr):
        bs = [int(byte, 16) for byte in addr.split(":")]

        if len(bs) != 6:
            raise Exception("Malformed MAC address")

        return bs

    def _byte_string_to_addr(self, byte_string):
        return ':'.join(map(lambda x: "%02x" % x, byte_string))

class IpPool(AddressPool):
    def _addr_to_byte_string(self, addr):
        bs = [int(byte) for byte in addr.split(".")]

        if len(bs) != 4:
            raise Exception("Malformed IP address")

        return bs

    def _byte_string_to_addr(self, byte_string):
        return '.'.join(map(str, byte_string))