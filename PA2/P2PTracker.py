import socket
import argparse
import threading
import sys
import hashlib
import time
import logging


#TODO: Implement P2PTracker
class Tracker:
	def __init__(self):
		self.port = 5100
		self.ip = "localhost"
		self.name = "P2PTracker"
		self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
		self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
		self.connections = []
		self.chunk_list = []
		#self.ip = "127.0.0.1"
		self.socket.bind(("127.0.0.1", int(self.port)))
  
		logging.basicConfig(filename="logs.log",format="%(message)s",filemode="a")
		self.logger = logging.getLogger()
		self.logger.setLevel(logging.DEBUG)
		#self.logger.info("Hello from tracker")
	def listen(self):
		#self.socket.bind(("127.0.0.1", int(self.port)))
		self.socket.listen()

		while True:
			connection, address = self.socket.accept()
			self.connections.append((connection, address[1]))
			#print(f"Accepted connection from {address}")
			t = threading.Thread(target=self.handle_client, args=(connection, address)).start()
			#t.start()
			#t.join()
   
	def update_chunks(self, data):
		#format: (index, (ip_address, port_number))
		self.chunk_list.append( (data[1], (data[2],data[3])) )
		print("NEW LIST", self.chunk_list)
  
	def find_chunk(self, data):
		command = "GET_CHUNK_FROM,"+data[1]
		location_data = ""
		for i in range(len(self.chunk_list)):
			if data[1] == self.chunk_list[i][0]:
				location_data = location_data + "," + self.chunk_list[i][1][0] + "," + self.chunk_list[i][1][1]
				#command = command + 
		if location_data == "":
			#case where nothing is found
			self.logger.info("P2PTracker,CHUNK_LOCATION_UNKNOWN,"+data[1])
			return "CHUNK LOCATION UNKNOWN,"+data[1]
		else:
			self.logger.info("P2PTracker," + command + location_data)
			return command+location_data
   
	def handle_client(self, connection, address):
		while True:
			try:
				data = connection.recv(1024)
				data = data.decode()
				segmented_data = data.split(",")
				if segmented_data[0] == "LOCAL_CHUNKS":
					self.update_chunks(segmented_data)
				if segmented_data[0] == "WHERE_CHUNK":
					command = self.find_chunk(segmented_data)
					connection.send(command.encode())
     
			except socket.error:
				break

		print(f"Connection from {address} closed.")
		self.connections.remove((connection,address[1]))
		connection.close()
  
	def start(self):
		listen_thread = threading.Thread(target=self.listen)
		listen_thread.start()
  

if __name__ == "__main__":
	tracker = Tracker()
	tracker.start()
	#tracker.listen()