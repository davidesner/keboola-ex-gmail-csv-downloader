import sys, os, shutil, pprint, csv, traceback, json, datetime, pip, gzip, base64, zipfile
from time import mktime
from time import sleep



pip.main(['install', 'requests'])

import requests

class Processor:
	
	
	def __init__(self, logging):
		self.logging = logging
	
	
	
	
	
	
	def unzip(self, zipFiles, folder):

	    txts = set()
	
	    # pysftp 0.2.9 and newer
	    # cnopts = pysftp.CnOpts()
	    # cnopts.hostkeys = None
	
	    for filename in zipFiles:
	                
	        self.logging.info('Unzipping: ' + filename)
	        try:
	            with zipfile.ZipFile(filename, 'r') as f:
	                for item in f.namelist(): 
	                        f.extract(item, folder)
	                        txts.add(item)
	                    
	        except:
	            raise RuntimeError('cannot unzip: ' + filename)
	
	    return txts   



