"""
xml_helper.py - functions for parsing and writing XML

Copyright (C) 2017 Sultan Qasim Khan <Sultan.QasimKhan@nccgroup.trust>

This file is part of the nOBEX Python package.

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program.  If not, see <http://www.gnu.org/licenses/>.
"""

from xml.etree import ElementTree

def escape_ampersands(s):
    # Terrible hack to work around Python getting mad at things like
    # <foo goo="Moo & Roo" />
    us = str(s, encoding='utf-8')
    us2 = '&amp;'.join(us.split('&'))
    return bytes(us2, encoding='utf-8')

def parse_xml(xml_str):
    try:
        root = ElementTree.fromstring(xml_str)
    except ElementTree.ParseError:
        root = ElementTree.fromstring(escape_ampersands(xml_str))
    return root
