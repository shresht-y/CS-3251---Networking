
import socket
import argparse
import threading
import sys
import hashlib
import time
import logging

#connections = []

def read_file(path):
    output = []
    path = path + "/local_chunks.txt"
    local_file = open(path, "r")
    chunk_data = local_file.read()
    lines =  chunk_data.splitlines()
    local_file.close()
    for line in lines:
        splitted = line.split(",")
        output.append((splitted[0], splitted[1]))
    return output

def update_tracker(local_chunks, logger, name,tracker_socket,transfer_port):
    print("LOCAL CHUNKS: ", local_chunks)
    for line in local_chunks:
        if line[1].strip() != "LASTCHUNK":
            command = "LOCAL_CHUNKS," + line[0] + ",localhost," + transfer_port
            logger.info(name+","+command)
            tracker_socket.send(command.encode())
            time.sleep(1)
            
            
def get_missing_chunks(local_chunks):
    total_chunks = int(local_chunks[-1][0])
    missing_chunks = []
    existing_chunks = []
    for i in range(total_chunks):
        missing_chunks.append(i+1)
    
    for chunk in local_chunks:
        existing_chunks.append(int(chunk[0]))
    existing_chunks.pop()
    output = []
    for chunk in missing_chunks:
        if chunk not in existing_chunks:
            output.append(chunk)
    return output
    
def update_local_chunks_file(new_chunk_index,folder):
    path = folder + "/local_chunks.txt"
    local_file = open(path, "r")
    chunk_data = local_file.read()
    lines =  chunk_data.splitlines()
    local_file.close()
    for i in range(len(lines)):
        index = lines[i][0]
        index = int(index)
        if int(new_chunk_index) <= index:
            l = str(new_chunk_index) + ",chunk_" + str(new_chunk_index)
            lines.insert(i,l)
            break
    for i in range(len(lines)):
        if lines[i] == lines[-1]:
            lines[i] = lines[i].strip()
        else:
            lines[i] = lines[i].strip() + " \n"
    local_file = open(path, "w")
    local_file.writelines(lines)
    local_file.close()
        
    
  
def get_chunks(local_chunks,logger,name,tracker_socket,client_socket,folder,req_ip,transfer_port):
    missing_chunks = get_missing_chunks(local_chunks)		
    chunk_locations = []
    while len(missing_chunks)>0:
        index = missing_chunks.pop()
        command = "WHERE_CHUNK," + str(index)
        logger.info(name+","+command)
        tracker_socket.sendall(command.encode())
        response = tracker_socket.recv(1024).decode()
        response = response.split(",")
        if response[0] == "GET_CHUNK_FROM":
            #only case where we do anything, will while loop until a location for all chunks are found
            chunk_locations.append( (response[1], response[2:]) )
        else:
            missing_chunks.insert(0, int(index))
    #print(chunk_locations)
    time.sleep(3)
    
    for chunk in chunk_locations:
        index = chunk[0]
        ip = chunk[1][0]
        port = chunk[1][1]
        client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        client_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        client_socket.connect((ip, int(port)))
        command = "REQUEST_CHUNK," + index
        logger.info(str(name + "," + command + "," + ip + "," + port))
        client_socket.send(command.encode())
        total_bytes = client_socket.recv(512).decode()
        total_bytes = int(total_bytes)
        bytes_read = 0
        
        path = folder + "/chunk_" + index
        
        new_file = open(path, "wb")
        
        data_left = True
        while bytes_read<total_bytes:
            seg = client_socket.recv(512)
            new_file.write(seg)
            bytes_read = new_file.tell() - bytes_read
            
        new_file.close()
        command = "LOCAL_CHUNKS," + chunk[0] + "," + req_ip + "," + transfer_port
        logger.info(name + "," + command)
        tracker_socket.sendall(command.encode())
        update_local_chunks_file(chunk[0], folder)
        #tracker_socket.close()
        client_socket.close()
        time.sleep(3)
   
def handle_client(connection,address,folder):
    data = connection.recv(1024)
    data = data.decode()
    data = data.split(",")
    
    print("DATA: ", data)
        
    path = folder + "/chunk_" + data[1]
        
    partitions = []
    with open(path, 'rb') as chunk_file:
        while True:
            segment = chunk_file.read(1024)
            if not segment:
                size = str(chunk_file.tell())
                break
            partitions.append(segment)
                
    connection.send(size.encode())
    time.sleep(1)
    for seg in partitions:
        connection.send(seg)
    chunk_file.close()

           


if __name__ == "__main__":
	parser = argparse.ArgumentParser()
	parser.add_argument('-folder', type=str, required=True)
	parser.add_argument('-transfer_port', type=str, required=True)
	parser.add_argument('-name', type=str, required=True)
	args = parser.parse_args()
	#declare initial variables
	name = args.name
	transfer_port = args.transfer_port
	folder_path = args.folder
	#connections = []
	tracker_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
	local_chunks = read_file(folder_path)
	ip = "localhost"
	logging.basicConfig(filename="logs.log",format="%(message)s",filemode="a")
	logger = logging.getLogger()
	logger.setLevel(logging.DEBUG)
	
	#connect to tracker and send current chunks 
	tracker_socket.connect((ip, 5100))
	#connections.append((tracker_socket, 5100))
	update_tracker(local_chunks, logger,name,tracker_socket,transfer_port)
	
	#create a socket to communicate with other clients
	client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
	client_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
	#start the thread to start recieving chunks 
	t = threading.Thread(target=get_chunks, args=(local_chunks,logger,name,tracker_socket,client_socket,folder_path,ip,transfer_port))
	t.start()
 
	#now listen to and service requests 
	service_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
	service_sock.bind((ip, int(transfer_port)))
	service_sock.listen()
	while True:
		connection, address = service_sock.accept()
		handle_client(connection, address,folder_path)
	
	
 
	