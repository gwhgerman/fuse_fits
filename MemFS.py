'''
Created on 30 Nov 2020

@author: ger063
'''
#!/usr/bin/env python

from __future__ import with_statement

import os
import sys
import errno
import stat
import time
import struct
import numpy as np
from io import BytesIO


from fuse import FUSE, FuseOSError, Operations
from datetime import datetime
from astropy.units.equivalencies import dimensionless_angles
from scipy.io.matlab.miobase import arr_dtype_number
from os_ken.services.protocols.bgp.operator.commands import root

HDR_BASESIZE = 2880

class MemFS(Operations):
    '''
    classdocs
    '''


    def __init__(self, HDUList, root,DEBUG):
        '''
        Constructor
        '''
        print("IN MemFS INIT")
        self.HDUList = HDUList
        self.filesize = HDUList[0].filebytes()
        self.root = root
        if (os.path.exists(root) != True):
            os.mkdir(root)
            
        self.test1_content = "Hello from test1\n"
        self.test2_content = "Hello from test2\n"
        self.DEBUG = DEBUG

    # Helpers
    # =======

    def _full_path(self, partial):
        if partial.startswith("/"):
            partial = partial[1:]
        path = os.path.join(self.root, partial)
        return path
    
    def _flattenRecurse(self,arr):
        ''' Flatten an n dimensional list or ndarray - this is recursive! 
            Use only for debugging
        '''
        if isinstance(arr,(list,np.ndarray)):
            for sub in arr:
                yield from self._flatten(sub)
        else:
            yield arr
            
    def _flatten(self, arr):
        '''
            Assumes a numpy n (>1) dim array and flattens it.
        '''
        arr.flatten()
        
        return arr
        
        
            

    # Filesystem methods
    # ==================

    def access(self, path, mode):
        if self.DEBUG:
            print ("IN ACCESS FUSE")
        full_path = self._full_path(path)
        if not os.access(full_path, mode):
            raise FuseOSError(errno.EACCES)

    def chmod(self, path, mode):
        full_path = self._full_path(path)
        return os.chmod(full_path, mode)

    def chown(self, path, uid, gid):
        full_path = self._full_path(path)
        return os.chown(full_path, uid, gid)

    def getattr(self, path, fh=None):
        #t1=datetime.now().strftime("%b %d %H:%M")
        if self.DEBUG:
            print ("IN GETATTR FUSE")
        t1 = time.time()
        stats = {
            'st_atime': t1,
            'st_ctime': t1,
            'st_gid': os.getgid(),
            'st_mode': stat.S_IFREG | 0o644,
            'st_mtime': t1,
            'st_nlink':1,
            'st_size': self.filesize,
            'st_uid': os.getuid()
            }
        if (path.endswith("/")):
            stats['st_mode'] = stat.S_IFDIR | 0o755
            stats['st_nlink'] = 2
            stats['st_size'] = 0
            
        return stats
        
    def readdir(self, path, fh):
        if self.DEBUG:
            print ("IN READDIR FUSE")
        full_path = self._full_path(path)

        dirents = ['.', '..']
        if os.path.isdir(full_path):
            #dirents.extend(os.listdir(full_path))
            #dirents.extend(["testfile1.txt","testfile2.txt"])
            dirlisting = os.path.basename(self.HDUList._file.name)
            dirents.extend([dirlisting])
        for r in dirents:
            yield r

    def readlink(self, path):
        if self.DEBUG:
            print ("IN READLINK FUSE")
        pathname = os.readlink(self._full_path(path))
        if pathname.startswith("/"):
            # Path name is absolute, sanitize it.
            return os.path.relpath(pathname, self.root)
        else:
            return pathname

    def mknod(self, path, mode, dev):
        return os.mknod(self._full_path(path), mode, dev)

    def rmdir(self, path):
        full_path = self._full_path(path)
        return os.rmdir(full_path)

    def mkdir(self, path, mode):
        return os.mkdir(self._full_path(path), mode)

    def statfs(self, path):
        full_path = self._full_path(path)
        stv = os.statvfs(full_path)
        return dict((key, getattr(stv, key)) for key in ('f_bavail', 'f_bfree',
            'f_blocks', 'f_bsize', 'f_favail', 'f_ffree', 'f_files', 'f_flag',
            'f_frsize', 'f_namemax'))

    def unlink(self, path):
        return os.unlink(self._full_path(path))

    def symlink(self, name, target):
        return os.symlink(name, self._full_path(target))

    def rename(self, old, new):
        return os.rename(self._full_path(old), self._full_path(new))

    def link(self, target, name):
        return os.link(self._full_path(target), self._full_path(name))

    def utimens(self, path, times=None):
        return os.utime(self._full_path(path), times)

    # File methods
    # ============

    def open(self, path, flags):
        if self.DEBUG:
            print ("IN OPEN FUSE")
        full_path = self._full_path(path)
        if (full_path.endswith('.fits')):
            return os.open(self.root,flags)
        return os.open(full_path, flags)

    def create(self, path, mode, fi=None):
        if self.DEBUG:
            print ("IN CREATE FUSE")
        full_path = self._full_path(path)
        return os.open(full_path, os.O_WRONLY | os.O_CREAT, mode)
    

    def read(self, path, length, offset, fh):
        ''' Present the HDUList as a FITS file '''
        if self.DEBUG:
            print ("IN READ FUSE")
        if (path.endswith(".fits")):
            vfile = BytesIO()
            for fits_obj in self.HDUList:
                header = []
                data = np.array([])
                key = ""
                # process the header
                for key in fits_obj.header:
                    # substitute HDU values with appropriate FITS variable
                    if (key == "SIMPLE"):
                        fits_obj.header[key] = 'T' if (fits_obj.header[key]) else 'F'
                    # All lines of the header must be 80 char length
                    line = "%s  =  %s" % (key,fits_obj.header[key])
                    line_size = len(line)
                    for i in range (80-line_size):
                        line += " "
                    vfile.write(line.encode('utf-8'))
                # Last field should be 'END'
                if not (key.startswith("END")):
                    vfile.write("END".encode('utf-8') + " ".encode('utf-8')*77)
                # header must be of size 2880 bytes or multiple of
                hdr_size = len(vfile.getvalue())
                pad = (HDR_BASESIZE - hdr_size) if (hdr_size < HDR_BASESIZE) else (HDR_BASESIZE -(hdr_size % HDR_BASESIZE))
                for i in range(pad):
                    vfile.write(b'\x20')
                hdr_size = len(vfile.getvalue())
                # process data
                data_size=0
                incr = int(abs(fits_obj.header["BITPIX"])/8) 
                if (len(fits_obj.data)>0):
                    data = self._flatten(fits_obj.data)
                    vfile.write(data)
                data_size = hdr_size+(incr*data.size)                  
                # data must be of size 2880 bytes or multiple of
                pad = (HDR_BASESIZE - data_size) if (data_size < HDR_BASESIZE) else (HDR_BASESIZE - (data_size % HDR_BASESIZE))
                for i in range(pad):
                    vfile.write(b'\x00')
        return vfile.getvalue()[offset:offset+length]
                            
        
    def write(self, path, buf, offset, fh):
        os.lseek(fh, offset, os.SEEK_SET)
        return os.write(fh, buf)

    def truncate(self, path, length, fh=None):
        full_path = self._full_path(path)
        with open(full_path, 'r+') as f:
            f.truncate(length)

    def flush(self, path, fh):
        if self.DEBUG:
            print ("IN FLUSH FUSE")
        return os.fsync(fh)

    def release(self, path, fh):
        if self.DEBUG:
            print ("IN RELEASE FUSE")
        return os.close(fh)

    def fsync(self, path, fdatasync, fh):
        print ("IN FSYNC FUSE")
        return self.flush(path, fh)


def main(mountpoint, root):
    print ("In MAIN FUSE")
    FUSE(MemFS([],root), mountpoint, nothreads=True, foreground=True)

if __name__ == '__main__':
    main(sys.argv[2], sys.argv[1])