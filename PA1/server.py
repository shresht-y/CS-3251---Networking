import socket
import threading
import sys 
import argparse
from datetime import datetime, timedelta



client_list = []
lock = threading.Lock()
#client returns two things:
#a socket object - use to connect with the client 

def send_message(message,exclude):
    lock.acquire()
    if exclude == None:
        for client in client_list:
            client[1].send(message.encode("utf-8"))
    else:
        for client in client_list:
            if client[1] != exclude:
                client[1].send(message.encode("utf-8"))
    lock.release()

def send_dm(receiver_username, message):
    lock.acquire()
    for client in client_list:
        if client[0] == receiver_username:
            client[1].send(message.encode("utf-8"))
    lock.release()

def add_client(username, socket):
    lock.acquire()
    client_list.append((username, socket))
    lock.release()
    
def remove_client(username, socket):
    lock.acquire()
    for i in range(len(client_list)):
        if client_list[i][0] == username and client_list[i][1] == socket:
            client_list.pop(i)
            break
    lock.release()

def accept(server_socket):
    socket, addr = server_socket.accept()
    #print("<server> Accepting client connection from ip: ", addr[0], " port: ", addr[1])
    #sys.stdout.flush()
    return socket, addr

def process_message(message):
    if message == ":)":
        return "[feeling happy]"
    elif message == ":(":
        return "[feeling sad]"
    elif message == ":mytime":
        curr_time = datetime.now()
        return " "+curr_time.strftime("%a %b %d %H:%M:%S %Y")
    elif message == ":+1hr":
        hour_time = datetime.now() + timedelta(hours=1)
        return " "+hour_time.strftime("%a %b %d %H:%M:%S %Y")
    else:
        return message
    return message

    
def client_thread_handler(client_socket, client_addr, disp_name):
    #print(disp_name, "joined the chatroom")
    #sys.stdout.flush()
    open_connection = True
    while open_connection:
        request = client_socket.recv(4096).decode("utf-8")
        #print(disp_name, ": ", request)
        #sys.stdout.flush()
        request = process_message(request)
        check_dm = request[:3]
        
        if request == ":Exit":
            close_message = ":Exit"
            client_socket.send(close_message.encode("utf-8"))
            open_connection = False  
            left_message = disp_name+" left the chatroom"
            print(left_message)
            sys.stdout.flush()
            send_message(left_message, client_socket)
            remove_client(disp_name, client_socket)
        elif check_dm == ":dm":
            #sending a dm case
            request_split = request.split()
            receiver = request_split[1]
            dm_message = request_split[2:]
            dm_message = ' '.join(dm_message)
            full_message = disp_name + " to " + receiver + ": "+dm_message
            print(full_message)
            sys.stdout.flush()
            dm = disp_name+": "+dm_message
            send_dm(receiver, dm)            
        else:
            chat = disp_name+": "+request
            print(chat)
            sys.stdout.flush()
            #client_socket.send(chat.encode("utf-8"))
            send_message(chat, client_socket)
  
    client_socket.close()
    

#TODO: Implement all code for your server here
def __main__(port_input, passcode):
    #create the socket
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_ip = "127.0.0.1"
    port = port_input
    password = passcode
    accepting_connections = True 
    server.bind((server_ip, int(port)))
    client_list = []
    
    #listen for connections - stalls the thread until a connection is recieved 
    start_str = "Server started on port "+port+". Accepting connections"
    print(start_str)
    sys.stdout.flush()
    server.listen()
    
    #Want to infinite loop and accept connections 
    while accepting_connections:
        client_socket, client_addr = accept(server)
        #client_list.append(client_socket)
        
        client_values = client_socket.recv(4096).decode("utf-8")
        #client values = "port,username,password"
        client_values = client_values.split(",")
        if client_values[2] == passcode:
            server_vals = "1,"+port
            client_socket.send(server_vals.encode("utf-8"))
            
            t = threading.Thread(target=client_thread_handler, args=(client_socket, client_addr, client_values[1]))
            t.start()
            
            #send a join message to all clients
            join_message = client_values[1]+" joined the chatroom"
            send_message(join_message, None)
            
            add_client(client_values[1], client_socket)
            
            print(join_message)
            sys.stdout.flush()
            
            #client_list.append(client_socket)
            
        else:
            #case where passcode is wrong
            client_socket.send("0".encode("utf-8"))
            
    
    server.close()
    


    
# Use sys.stdout.flush() after print statemtents

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('-start', action='store_true')
    parser.add_argument('-port', type=str, required=True)
    parser.add_argument('-passcode', type=str, required=True)
    args = parser.parse_args()
    #print("port", args.port)
    #print("passcode", args.passcode)
    __main__(args.port, args.passcode)