# importing the necessary packages
import os
import argparse
from socket import *
import threading
from threading import BoundedSemaphore
import time
from urlparse import urlparse

userlock1 = threading.Lock()

#Creating client socket alongnside its buffer size and port
clientSocket = socket(AF_INET,SOCK_STREAM)
buf=2048
serverPort = 80
#myThread will initialize threads
class myThread (threading.Thread):
	#here startbyte and endbyte will give us the content length requirements for getting the data
	def __init__(self, startByte, endByte, file):
		threading.Thread.__init__(self)
		self.startByte = startByte
		self.endByte = endByte
		self.file = file
	
	#Run function that will be invoked when we will call start and the threads will further call send request method
	def run(self):
		startByte = self.startByte
		endByte = self.endByte
		file = self.file
		#print "Starting " + str(threading.current_thread())+'\n'
		send_request(startByte,endByte,self.file)
		
		#print "Exiting " + str(threading.current_thread())+'\n'

#function called by thread so that threads may download the required content parallely
def send_request(startByte, endByte, file):
	#checking for the resume functionality if some file already exists then we don't need to download it
	if (int(startByte)) != int(endByte):
		message ='GET '+str(filePath)+' HTTP/1.1\r\nHOST: '+hostname+'\r\nRange: bytes='+str(startByte)+'-'+str(endByte)+'\r\n\r\n'
		#client socket made for receiving data
		clientSocket = socket(AF_INET,SOCK_STREAM)
		clientSocket.connect( (serverIP,serverPort))
		#print file
		f = open(file,'ab')#creating a temporary file under the mode of append
		clientSocket.send(message)#here message contains the GET request header
		data = clientSocket.recv(buf)
		data = data.split('\r\n\r\n')[1]#to remove the header from the data that we are receiving
		prev = 0
		
		while(data):
			f.write(data)
			#print "waiting..: "
			data = clientSocket.recv(buf)
			ending_time = time.time() - starting_time
                        #print "starting time: ",starting_time
                        #print "ending time",ending_time % 60
                        #print "time interval",timeinterval
			if container.acquire(False):
				if float(ending_time%60) >= float(timeinterval):
					try:
						#os.system("cls")
						displayMatrix(int(endByte)-int(startByte),file,prev,starting_time,ending_time)
						ending_time -= starting_time
						container.release()
					except:
						print ""
				else:
					print ""
			prev = os.path.getsize(file)
		clientSocket.close()
		#print "download finished"
	else:
		#print "Already present"
		print ""
	

# construct the argument parse and parse the arguments using argparse
ap = argparse.ArgumentParser()
ap.add_argument("-n", "--noofConnections", required=True)
ap.add_argument("-i", "--timeinterval", required=True)
ap.add_argument("-c", "--connectionType", required=True)
ap.add_argument("-f", "--webAddress", required=True)
ap.add_argument("-o", "--filetoStore", required=True)
ap.add_argument("-r", "--resume", required=False)
args = vars(ap.parse_args())
#assigning values to variables
noofConnections = args["noofConnections"]
timeinterval = args["timeinterval"]
connectionType = args["connectionType"]
webAddress = args["webAddress"]
filetoStore = args["filetoStore"]
#using urlparse and parsing the web address for getting IP address, hostname, its path
o = urlparse(webAddress)
hostname = o.netloc
serverIP = gethostbyname(hostname)
filePath = o.path
container = BoundedSemaphore(int(noofConnections))
#checking the resume functionality
if args["resume"] == None:
	resume = False
else:
	resume = True
	
#message request for header of the required file
message = 'HEAD '+str(filePath)+' HTTP/1.1\r\nHOST: '+hostname+'\r\nRange: bytes=0-\r\n\r\n'
file = os.path.basename(filePath)#for getting the base name i.e, what file are we downloading e.g, image.png or worddocument.doc

#getting the starting time before sending the request
starting_time = time.time()
#TCP funtion which will be called if the USER wants to send the data by TCP protocol
def tcp():
	#making a client socket for getting its header
	clientSocket.connect( (serverIP,serverPort))
	clientSocket.send(message)
	data = clientSocket.recv(buf)
	reply = ''
	while(data):
		#appending in reply string all the data which we receive by the size specified by buffer size
		reply += data	
		data = clientSocket.recv(buf)#retrieving the buf size data
	clientSocket.close()

	#temporary variable spliting each line in header
	temp = reply.split('\r\n')
	contentTemp = dict()
	for i in temp[1:]:#as first line contains unnecessary header
		key = i.split(": ")
		try:
			contentTemp[key[0]] = key[1]
		except:
			#for catering those header lines which cannot be split by ": "
			print ""
	
	#checking if the website we accessed is supported by multiple threads
	if(contentTemp["Accept-Ranges"] == "bytes"):
		thread=[]
		chunk = int(int(contentTemp['Content-Length'])/int(noofConnections))#dividing the total file size into parts
		for i in range(int(noofConnections)):#for creating that many threads of file
			#if we wanted to resume
			if resume:
				try:
					f = open(str(i)+file,'r')
					statinfo = os.stat(str(i)+file)#Getting size of a existing file to send startbyte after that size
					thread.append(myThread(str((i*chunk)+statinfo.st_size - 1) ,str(((i+1)*chunk)-1 ),str(i)+file))
				except:
					#if even in resume some files are present but not all
					thread.append(myThread(str(i*chunk) ,str(((i+1)*chunk)-1 ),str(i)+file))
			#if we want to download from start
			else:
				try:#we dont want to resume but file is already present
					f= open(str(i)+file,'r')
					f.close()
					os.remove(str(i)+file)
				except:
					print ""
				thread.append(myThread(str(i*chunk) ,str(((i+1)*chunk)-1 ),str(i)+file))
			#starting all threads
			thread[i].start()
		
		#staritng all threads
		for i in range(int(noofConnections)):
			thread[i].join()
		
		#here adding the file path of download to the file name so that file gets downloaded on that specific directory
		completeName = os.path.join(filetoStore, file)	
		#opening that file in append mode
		outputFile = open(completeName, "ab")
		
		tempfiles = list()#here we will get all the temporary files created by the threads
		for i in range(int(noofConnections)):
			tempfiles.append(str(i)+file)
		
		for temp in tempfiles:
			f = open(temp,'rb')#open the temporary file
			outputFile.write(f.read())
			f.close()
			os.remove(temp)#removing the temporary file from the system after writing its data
	else:
		#if our file doesnot support multithreading then we can just create a single thread and download that file
		if resume:
			try:
				f= open(file,'r')
				statinfo = os.stat(file)#Getting size of a existing file to send startbyte after that size
				thread1 = myThread(str(statinfo.st_size - 1) ,contentTemp['Content-Length'],str(file))
			except:
				thread1 = myThread(0, contentTemp['Content-Length'],str(file))
		else:
			try:#if not resume but file was already present
				f= open(file,'r')
				f.close()
				os.remove(file)
			except:
				print ""
			thread1 = myThread(0, contentTemp['Content-Length'],str(file))
	#print "End program"


def displayMatrix(size,file,prev,starting_time,ending_time):
	userlock1.acquire()	
	#os.system("cls")
	csize = os.path.getsize(file)
	print "Connection ",str(threading.current_thread())," ",str(csize),"/",str(size),", download speed: ",abs((int(csize-prev-1)/1000)/float(timeinterval))
	userlock1.release()
	
def udp():
	print("Such a connection is not possible with UDP")


if (str.lower(connectionType) == "tcp"):
	tcp()
else:
	udp()
