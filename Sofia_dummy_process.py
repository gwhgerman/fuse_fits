'''
This is a small test script to test out MemFS with some FITS data

Created on 10Dec 2020
@author: ger063
'''
#!/usr/bin/env python

import os
import sys

from astropy.io import fits
import MemFS
  
if __name__ == "__main__":
   
    hdr = {}
    data = [] 
    data1D = []
    # Read in the FITS file as if it were a regular file
    FITSfile = "/home/ger063/tmp/inMemFITS.fits"
#    FITSfile = "/home/ger063/check.bin"
#    FITSfile = "/home/ger063/src/sofia/Julien2.fits"
    with fits.open(FITSfile) as hdul:
        hdul.info()
        # Do some checks
        hdr = hdul[0].header
        data = hdul[0].data
        data1D = data.ravel()
    print("Done!")
    
    
