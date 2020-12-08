# fuse_fits

Basic python modules to serve up FITS datafiles as FUSE in-memory 
arrays.

The main module to import into your code is in MemFS.py.

Ingest.py is an example module - run as:

python3 Ingest.py <path_to_FITS_file> <path_to_dummy_dir_to_mount>

Eg if 'mountpoint' is '$HOME/test', the FITS file read in will appear in 
that directory as a file, but in reality is in memory. 

Standard ops such as 'cat' will appear to read the file, but are actually 
passed the data in mem.

Note the example in Ingest can run in a thread (see Ingest.thread_FUSE. 
It's up to you how you want to terminate it!
