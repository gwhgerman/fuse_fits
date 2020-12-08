'''
This is a small test script to test out MemFS with some FITS data

Created on 3Dec 2020
@author: ger063
'''
#!/usr/bin/env python

import os
import sys
import logging
import time
import threading

from fuse import FUSE, FuseOSError, Operations

import MemFS

from astropy.io import fits

DEBUG=True
#TESTFILE = "/home/ger063/Downloads/l1448_13co.fits"
    
def thread_FUSE(hdul,root,mountpoint):
    ''' Run FUSE mount in a thread '''
    if DEBUG:
        logging.info("Thread FUSE: starting")
    # To actually run in a thread, set 'foreground=False', but note that you'll have to
    # use 'ps' to find and kill the fuse process if you do!
    FUSE(MemFS.MemFS(hdul,root,DEBUG), mountpoint, direct_io=True, nothreads=True, foreground=True, big_writes=True)
    if DEBUG:
        logging.info("Thread FUSE: finishing")
    
def usage():
    
    print("Usage: python Ingest.py <path_to_FITS_file> <path_to_dummy_dir_to_mount>\n")
    print(" - dummy dir must exist\n")

if __name__ == "__main__":
    ''' This tests the FUSE interface by simply loading a FITS file into mem (via astropy)
        and then passing it out again as a memory obj when a READ is called on the dummy 
        directory's file.
        
        Eg if 'mountpoint' is '$HOME/test', the FITS file read in will appear in that directory 
        as a file, but in reality is in memory. Standard ops such as 'cat' will appear to read the 
        file, but are actually passed the data in mem.
    '''
    
    if len(sys.argv) < 3:
        usage()
        sys.exit()
    # Use the user's FITS file
    TESTFILE = sys.argv[1]
    # this is the 'dummy' directory that FUSE will serve up as a replacement
    mountpoint = sys.argv[2]
    # not used in this implementation
    root = "/tmp"
    
    format = "%(asctime)s: %(message)s"
    logging.basicConfig(format=format, level=logging.INFO,
                        datefmt="%H:%M:%S")
    mem_fits = None
    thr = None
    
    with fits.open(TESTFILE) as hdul:
        hdul.info()
        for key in hdul[0].header:
            print("%s : %s" % (key,hdul[0].header[key]))
        #print(hdul[0].data)
        #mem_fits = MemFS.MemFS(hdul,mountpoint)
            
        #FUSE(MemFS.MemFS(hdul,root), mountpoint, nothreads=True, foreground=True)
        if DEBUG:
            logging.info("Main    : before creating thread")
        thr = threading.Thread(target=thread_FUSE, args=(hdul,root,mountpoint))
        if DEBUG:
            logging.info("Main    : before running thread")
        thr.start()
        if DEBUG:
            logging.info("FUSE thread started")
        thr.join() 
    print("Done")
