# -*- coding: utf-8 -*-
"""
Created on Thu Feb 20 06:59:20 2014

@author: Crane Johnson


"""

import tarfile,sys,urllib2,datetime,time,tarfile,os,fnmatch,re,shutil
from optparse import OptionParser

backupLocation = 'http://aprfc.arh.noaa.gov/chpsgrids/'
chpsImportDir = 'import/'
count = 0



"""
	Function to create human readable filesizes
"""
def sizeof_fmt(num, suffix='B'):
    for unit in ['','Ki','Mi','Gi','Ti','Pi','Ei','Zi']:
        if abs(num) < 1024.0:
            return "%3.1f %s%s" % (num, unit, suffix)
        num /= 1024.0
    return "%.1f%s%s" % (num, 'Yi', suffix)


"""
	Function to download files with progress shown
"""
def downloadFile(url):
	file_name = url.split('/')[-1]
	u = urllib2.urlopen(url)
	f = open(file_name, 'wb')
	meta = u.info()
	file_size = int(meta.getheaders("Content-Length")[0])
	print "Downloading: %s Filesize: %s" % (file_name, sizeof_fmt(file_size))
	file_size_dl = 0
	block_sz = 8192
	while True:
		buffer = u.read(block_sz)
		if not buffer:
			break

		file_size_dl += len(buffer)
		f.write(buffer)
		status = r"%10d  [%3.2f%%]" % (file_size_dl, file_size_dl * 100. / file_size)
		status = status + chr(8)*(len(status)+1)
		print status,

	f.close()
	print
	if file_size == file_size_dl:
		return True
	else:
		return False


"""
	Match and remove
"""
def process_match(m):
    # Process the match here.
    return ''


"""
	Need to use optparse for compatibility reasons
"""

parser = OptionParser()
parser.add_option("-d", "--days",type = "int",dest="d",
					help="Number of days to download")
parser.add_option("-v", "--verbose",
                  action="store_true", dest="verbosity", default=False,
                  help="Flag for verbose output")
parser.add_option("-f", "--force",
                  action="store_true", dest="force", default=False,
                  help="Force file downloads from remote server")


(options, args) = parser.parse_args()


if not options.d:   # if filename is not given
	parser.error("Number of days to download is required\n")


startDate = datetime.datetime.now() -  datetime.timedelta(days = options.d)


"""
	Get a list of chps backup files stored on APRFC
"""

try:
	remotefile = urllib2.urlopen(backupLocation+'index.php')
	fileList = remotefile.read().split('\n')
	location = 'remote'
except urllib2.HTTPError, e:
	print('HTTPError = ' + str(e.code))
	print "Failed to get data from: {}".format(backupLocation)
	fileList = [f for f in os.listdir('.') if os.path.isfile(f)]
	location = 'local'
except urllib2.URLError, e:
	print('URLError = ' + str(e.reason))
	print "Failed to get data from: {}".format(backupLocation)
	fileList = [f for f in os.listdir('.') if os.path.isfile(f)]
	location = 'local'
except httplib.HTTPException, e:
	print('HTTPException')
	print "Failed to get data from: {}".format(backupLocation)
	fileList = [f for f in os.listdir('.') if os.path.isfile(f)]
	location = 'local'
except Exception:
	import traceback
	print('generic exception: ' + traceback.format_exc())
	print "Failed to get data from: {}".format(backupLocation)
	fileList = [f for f in os.listdir('.') if os.path.isfile(f)]
	location = 'local'




gridList = [k for k in fileList if 'chpsgrids' in k]
if options.verbosity:
	print "\n\nFiles on {} server:".format(location)

	for file in gridList:
		print "   {}".format(file)



print "\n\n{} chpsgrids tar files available on {} server".format(len(gridList),location)
print "Files will be move to here: {}".format(chpsImportDir)
print "{}/index.php?verbose=true\n".format(backupLocation)
print "\nThe most recent {} day(s) will be used (Starting at:{})".format(options.d,startDate.date())


"""
	Print Initial script status
"""
if options.force:
	print "Force backup Downloads"


"""
	Download the requested backup files
"""
for file in gridList:
	parts = file.split('.')
	dt=datetime.datetime.strptime(parts[1], '%Y%m%d')#.strftime("%s")
	if dt.date() >= startDate.date():
		if os.path.isfile(file) and not options.force:
			print "{} exists locally, skipping download".format(file)
		else:
			if downloadFile(backupLocation+file):
				count = count + 1
		tar = tarfile.open(file)
		tar.extractall('tmpTar')
		tar.close()




print "\n{} chpsgrids tar files downloaded".format(count)


"""
	Process the Tar Files
"""
p = re.compile(".*chpsgrids")
count = 0
if options.verbosity:
	print "\n\nFiles Moved:"
for root, dirs, files in os.walk('tmpTar'):
    for filename in files:
        fullName = os.path.join(root,filename)
    	newFullName = chpsImportDir+p.sub(process_match,fullName)
    	match = p.match(fullName)
        if match:
			if not os.path.exists(os.path.dirname(newFullName)):
				os.makedirs(os.path.dirname(newFullName))
			if options.verbosity:
				print "   File: {}".format(fullName)
				print "   To:   {}".format(newFullName)
				print
			try:
				shutil.copy2(fullName,newFullName)
			except:
				print "Failed to copy file into CHPS input directory: {}".format(fullName)
			count = count + 1

print "\n{} files copied to {} directory\n\n".format(count,chpsImportDir)

"""
	Delete the tmp directory
"""
try:
	shutil.rmtree('tmpTar')
except:
	print ""

