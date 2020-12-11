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

DEBUG=False
#TESTFILE = "/home/ger063/Downloads/l1448_13co.fits"

def extractFromFits(fitsfile):
    ''' Return the FITS hdr as a dict and the FITS data
        as a 3D array of floats.
    '''
    hdr = {}
    data3D =[[[]]]
    with fits.open(TESTFILE) as hdul:
        for key in hdul[0].header:
            hdr[key] = hdul[0].header[key]
            data3D = hdul[0].data
        hdul.info()
    return hdr,data3D
    
    
def thread_FUSE(hdr,data3D,root,mountpoint):
    ''' Run FUSE mount in a thread '''
    if DEBUG:
        logging.info("Thread FUSE: starting")
    # To actually run in a thread, set 'foreground=False', but note that you'll have to
    # use 'ps' to find and kill the fuse process if you do!
    FUSE(MemFS.MemFS(hdr,data3D,root,DEBUG), mountpoint, direct_io=True, nothreads=True, foreground=True, big_writes=True)
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
    # For testing, we use the user's FITS file
    # Normally you'd have the FITS fileheader in a dict, and your 
    # data in a 3D array.
    TESTFILE = sys.argv[1]
    # Extract the header and data
    header,data3D = extractFromFits(TESTFILE)
    
    # this is the 'dummy' directory that FUSE will serve up as a replacement
    mountpoint = sys.argv[2]
    # not used in this implementation
    root = "/tmp"
    
    form = "%(asctime)s: %(message)s"
    logging.basicConfig(format=form, level=logging.INFO,
                        datefmt="%H:%M:%S")
    thr = None
    
    if DEBUG:
        logging.info("Main    : before creating thread")
    thr = threading.Thread(target=thread_FUSE, args=(header,data3D,root,mountpoint))
    if DEBUG:
        logging.info("Main    : before running thread")
    thr.start()
    if DEBUG:
        logging.info("FUSE thread started")
    # As the thread doesn't terminate, this will never happen:
    thr.join()
    # Call this when you're done, otherwise use 'ps aux fuse' to find and 
    # kill the process
    os.system("fusermount -u %s" % mountpoint) 
    print("Done")
