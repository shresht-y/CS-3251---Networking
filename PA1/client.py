import socket
import threading
import sys 
import argparse

#TODO: Implement a client that connects to your server to chat with other clients here
def receive(client_socket):
    while True:
        #message = input("<client> Enter chat: ")
        #client_socket.send(message.encode("utf-8"))
        
        #get response from server
        server_message = client_socket.recv(4096)
        server_message = server_message.decode("utf-8")
        
        if server_message == ":Exit":
            #print("<client> Connection closed (Receive thread)")
            #sys.stdout.flush()
            #communicate(client_socket)
            break 
        else:
            print(server_message)
            sys.stdout.flush()
        
    #client_socket.close()
    

def communicate(client_socket):
    #open_connection = True
    while True:
        message = input()
        #client_socket.send(message.encode("utf-8"))
        #get response from server
        
        if message == ":Exit":
            #print("<client> Connection closed (Sending thread)")
            #sys.stdout.flush()
            client_socket.send(":Exit".encode("utf-8"))
            break
        else:
            client_socket.send(message.encode("utf-8"))
        
        #else:  
        #	print("<client> Request received, message: {server_response}")
        #	sys.stdout.flush()
    #client_socket.close()
        

def authenticate(client_socket, port, username, passcode):
    values = port+","+username+","+passcode
    #client_socket.send(port.encode("utf-8"))
    #client_socket.send(username.encode("utf-8"))
    client_socket.send(values.encode("utf-8"))
    server_vals = client_socket.recv(4096).decode("utf-8")
    return server_vals


def __main__(hostname, port, username, passcode):
    client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_ip = "127.0.0.1"
    server_port = port
    
    client_socket.connect((server_ip, int(server_port)))
    vals = authenticate(client_socket, port, username, passcode)
    if vals[0] == "1":
        vals = vals.split(",")
        print("Connected to", hostname, "on port", vals[1])
        sys.stdout.flush()
        #communicate(client_socket)
        t = threading.Thread(target=communicate, args=(client_socket,))
        r = threading.Thread(target=receive, args=(client_socket, ))
        t.start()
        r.start()
        #client_socket.close()
        t.join()
        r.join()
        
    else: 
        print("Incorrect passcode")
    
    client_socket.close()
    
    
# Use sys.stdout.flush() after print statemtents
if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('-join', action='store_true')
    parser.add_argument('-host', type=str, required=True)
    parser.add_argument('-port', type=str, required=True)
    parser.add_argument('-username', type=str, required=True)
    parser.add_argument('-passcode', type=str, required=True)
    args = parser.parse_args()
    __main__(args.host, args.port, args.username, args.passcode)