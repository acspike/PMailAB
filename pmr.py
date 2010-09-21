'''
Pegasus Mail Addressbook (*.PMR) File Format

Copyright (c) 2010 Aaron C Spike

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in
all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
THE SOFTWARE.
'''

import struct
from collections import namedtuple
import csv
from cStringIO import StringIO

class EndOfFile(Exception):
    pass
    
class NotEnoughData(Exception):
     def __init__(self, need, got):
         self.need = need
         self.got = got
     def __str__(self):
         return "wanted %s bytes but only found %s" % (self.need, self.got)

def strip_null(x):
    if isinstance(x,str):
        return x.strip('\x00')
    return x
    
class NamedStructReader(object):
    '''an object capable of reading a predefined struct from a file and turning it into useable named tuple'''
    def __init__(self, name, format, fields):
        self.name = name
        self.format = format
        self.fields = fields
        self.struct = struct.Struct(format)
        self.namedtuple = namedtuple(name, fields)
        def iteritems(this):
            for x in self.fields:
                yield (x, getattr(this, x))
        self.namedtuple.iteritems = iteritems
    def read(self, f):
        bytes = f.read(self.struct.size)
        try:
            items = self.struct.unpack(bytes)
            #strip null bytes because Python's struct module doesn't understand null terminated strings
            items = [strip_null(x) for x in items]
            return self.namedtuple._make(items)
        except struct.error:
            size = len(bytes)
            if size == 0:
                raise EndOfFile
            else:
                raise NotEnoughData(self.struct.size, len(bytes))
        
header_fields = ['name']
header_format = '28s100x'
header = NamedStructReader('Header', header_format, header_fields)

entry_fields = 'name company key street post phone fax notes email image'.split()
entry_format = '2x40s40s12s60s60s24s24s80s100s4x9s3x'
entry = NamedStructReader('Entry', entry_format, entry_fields)

class PMRFile(object):
    '''An iterable parser for PMR files
    stores the Addressbook name
    iterates over Addressbook Entries
    '''
    def __init__(self, pmrfile):
        if isinstance(pmrfile, basestring):
            pmrfile = open(pmrfile,'rb')
        self.file = pmrfile
        h = header.read(self.file)
        self.name = h.name
    def __del__(self):
        self.file.close()
    def __iter__(self):
        return self
    def next(self):
        try:
            return entry.read(self.file)
        except EndOfFile:
            raise StopIteration

def pmr2google(inputfile):
    '''convert a newly opened pmrfile object into a csv file suitable for import into Google Contacts'''
    
    outputfile = StringIO()
    writer = csv.writer(outputfile)
    
    #PMail doesn't distinguish between Home or Work phones/faxes
    #the appropriate type to use here could be argued, but this gets it into Google
    fields = ['Name','Company','Home Address','Other Address','Home Phone','Home Fax','Notes','E-mail Address']
    
    writer.writerow(fields)
    
    for e in inputfile:
        vals = [e.name, e.company, e.street, e.post, e.phone, e.fax, e.notes, e.email]
        writer.writerow(vals)
    
    return outputfile.getvalue()

if __name__ == '__main__':
    import sys
    
    inputfile = PMRFile(sys.argv[-1])
    print pmr2google(inputfile)
