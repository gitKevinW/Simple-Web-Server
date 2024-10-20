import select
import socket
import sys
import queue
import time, datetime
import re
from datetime import datetime
from datetime import timedelta
#\s*(GET)\s(/)(.*)\s(HTTP/1\.0)\s*

def log_request(address, request, response):
    ip = address[0]
    port = address[1]
    ipPort = str(ip) + ":" + str(port)
    
    request = str(request)
    response = str(response)
    
    if "\r\n" in request: #for windows
    #if request.endswith("\r\n"):
        requestSplit = request.split('\r\n')
        #print("requestSplit:", requestSplit)
    
    elif "\n" in request: #for linux
    #elif request.endswith("\n"): 
        requestSplit = request.split('\n')
        #print("requestSplit:", requestSplit)
    
    else:
        requestSplit = request.split('\n')
    
    if response.endswith("\r\n\r\n"): #for windows
        responseSplit = response.split("\r\n\r\n")
        
    elif response.endswith("\n\n"): #for linux
        responseSplit = response.split("\n\n")
    
    else:
        responseSplit = response.split("\n\n")

    
    date_time = datetime.now()
    date_time = date_time.astimezone()
    date = date_time.strftime("%a %b %d %X %Z %Y")
    
    log = (f"{date}: {ipPort} {str(requestSplit[0])}; {str(responseSplit[0])}")
    
    log = log.strip("\r\n")
    log = log.strip("\n")
    print(log)
    

def closeSocket(s):
    if s in inputs:  inputs.remove(s)
    if s in outputs: outputs.remove(s)
    s.close()
    
    if response_messages[s]:
        del response_messages[s]
    if request_message[s]:
        del request_message[s]

def badRequest():
    
    response = 'HTTP/1.0 400 Bad Request\r\n'
    return response

def currentChecker(request):
    
    if "get" in request.casefold():
        if bool(re.match(r"\s*(GET)\s(/)(.*)\s(HTTP/1\.0)\s*", request)):
            return 1 #its a get request and does not have a typo
        else:
            return -1 #its a get request but typo
    return 0 #its giberish

def checkConnection(connection):
    
    if 'connection' in connection.casefold():
        return 'keep-alive' in connection.casefold()
    else:
        return False

def splitRequest(request):
    
    singleNewLine = []
    
    if "\r\n\r\n" in request:
        doubleNewLine = request.split("\r\n\r\n")[:-1]
    
    elif "\n\n" in request:
        doubleNewLine = request.split("\n\n")[:-1]
        
    else:
        doubleNewLine = request.split("\n\n")
        
    return doubleNewLine
                
def validateRequest(data):
    return bool(re.match(r"\s*(GET)\s(/)(.*)\s(HTTP/1\.0)\s*", data))
                
    
def handleRequest(request, client_address, keep_alive):
    
    body = ''
    header = ''
    flag = 0
    
    requestValidity = validateRequest(request)
    
    if requestValidity:
        filename = request.split(' ')[1][1:] #extract filename from GET request
        
        try:
            with open(filename, 'r') as file: #opens the file and closes it after
                body = file.read()
                header = 'HTTP/1.0 200 OK\r\n'
                
        except FileNotFoundError:
            header = 'HTTP/1.0 404 Not Found\r\n'
    
    else:
        header = badRequest()
        flag = 1
        #'HTTP/1.0 400 Bad Request\r\nConnection: close\r\n\r\n'
    
    if flag == 0:
        if keep_alive:
            status = "Connection: keep-alive\r\n\r\n"
        else:
            status = "Connection: close\r\n\r\n"
    else:
        status = "Connection: close\r\n\r\n"
        
    response = header + status + body
    
    log_request(client_address, request, header)
    
    return response.encode(), status, flag
    
    

def main1(ip, port):
    
    # Create a TCP/IP socket
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    # Allow address reuse
    server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    # Set the socket to non-blocking mode
    server.setblocking(0)
    # Bind address, server_address is defined by the input
    server.bind((ip, port))
    # Listen for incoming connections
    server.listen(5)



    # Sockets to watch for readability
    global inputs 
    inputs = [server]
    
    # Sockets to watch for writability
    global outputs 
    outputs = []
    
    # Outgoing message queues (socket:Queue)
    global response_messages
    response_messages = {} #message queues for each client connection so if the client is not ready for writing it can still have the messages (our responses) saved in a queue
    
    # Incoming message
    global request_message
    request_message = {} #data buffers for saving incoming messages the clients are sending us, can be used to store partial data until it's a complete request

    timer_buffer = {} #buffer that keeps track of each client's timeouts
    timeout = timedelta(seconds = 31)
    flag = 0 #for when piping commands there is a bad request in the middle of it
    
    flag2 = 0 #for if there is garbage before the GET request
    
    while True:
        flag = 0
        
     # Wait for at least one of the sockets to be ready for processing
        readable, writable, exceptional = select.select(inputs, outputs, inputs, 3)

        current = datetime.now()
      
        for s in readable:
            if s is server:
                    # Accept new connection and append new connection socket
                    # to the list to watch for readability
                    connection, client_address = s.accept()
                    connection.setblocking(0)
                    inputs.append(connection)
                    response_messages[connection] = queue.Queue()
                    request_message[connection] = ''
                    timer_buffer[connection] = datetime.now()
            else:
                 # Receive message from the receiving buffer
                    message = s.recv(1024).decode()
                    if message:
                        timer_buffer[s] = datetime.now() #updates the timeout timer
                        
                     # If message is not empty, we add the read data
                     # to the message buffer
                        
                        request_message[s] += message
                        print(message)
                        
                        if request_message[s] == "\r\n\r\n" or request_message[s] == "\n\n": 
                            #to allow the user to spam the enter key without triggering Bad Request which you are NOT supposed to trigger bad request 400
                            request_message[s] = ''
                            continue
  
                        
                        lineCheck = currentChecker(message) #checks line by line if the get response is good or not (ignores garbage)
                        if lineCheck == -1: #if get response is not good bad request
                            bad = badRequest()
                            log_request(client_address, message, bad)
                            bad = bad + "Connection: close\r\n\r\n"
                            s.send(bytes(bad, 'utf-8'))

                            closeSocket(s)
                            continue

                        if request_message[s].endswith("\r\n\r\n") or request_message[s].endswith("\n\n"): # is complete (ends with "\r\n\r\n" or "\n\n"):
                            whole_message = request_message[s]
                         # Add connection socket s to the list for outputs,
                         # as we will send back messages
                         # Process the message into a response
                         # Add the response to the response queue
                            
                            split = splitRequest(whole_message) 

                            for double in split:
                                connectionType = checkConnection(double)
                                #in each stack checks the connection type
                                
                                response, connectionType, flag = handleRequest(double, client_address, connectionType)
                                
                                if flag == 0: 
                                    response_messages[s].put((response, connectionType))
                                if s not in outputs:
                                    outputs.append(s)
                                    
                                if flag == 1: #during piping in the middle  of a bunch of requests there is a bad one so need to close connection
                                    connectionType = "Connection: close\r\n\r\n"
                                    
                                    response_messages[s].put((response, connectionType))
                                    break;
                                    
                            request_message[s] = '' #for reset
                            timer_buffer[s] = datetime.now()

        for s in writable:
                # Get messages from response_messages[s]
            try:
                next_msg, keepAlive = response_messages[s].get_nowait()

                
            except queue.Empty:
                 # Check if timeout or connection is persistent
                 # or not, and close socket accordingly
                outputs.remove(s)
            else:
                 # Send messages and print logs if finished
                 # responding to a request
                s.send(next_msg)
                if keepAlive == "Connection: close\r\n\r\n" or keepAlive == "Connection: close\n\n":

                    closeSocket(s)
                    del timer_buffer[s]
                
        for s in exceptional:
            inputs.remove(s)
            closeSocket(s)
            del timer_buffer[s]

        for s in inputs:
            if s is not server and (current >= (timer_buffer[s] + timeout)):
                inputs.remove(s)
                if s in outputs:
                    outputs.remove(s)
                closeSocket(s)
                del timer_buffer[s]
                continue


if __name__ == '__main__':
    ip = sys.argv[1]
    port = int(sys.argv[2])
    main1(ip, port)