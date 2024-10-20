# Simple-Web-Server

In this program, I use the STREAM socket (i.e., supported by TCP) in Python to create a Simple Web Server (SWS), mimicking nginx-light in PicoNet but only supporting limited functionalities as
specified below, with select() supporting both persistent and non-persistent HTTP connections.

# Documentation

SWS (Simple Web Server) only supports the “GET /filename HTTP/1.0” command, and “Connection: keep-alive” and “Connection: close” request and response headers when supporting persistent HTTP connection. 

The request header is terminated by an empty line known as “\r\n”, where “\r” indicates a carriage return and “\n” is a (new) line feed.

If unsupported commands are received or in unrecognized format, SWS will respond to “HTTP/1.0 400 Bad Request” and close the connection immediately.

If the file indicated by the filename is inaccessible, SWS will return “HTTP/1.0 404 Not Found”. 

Such responses will be followed by the response header if any, an empty line, indicating the end of the response.

For successful requests, SWS will respond “HTTP/1.0 200 OK”, followed by the response header if any, an empty line indicating the end of the response header, and the content of the file.

In both “200” and “404” cases, if the client requests a persistent connection, SWS will keep the connection open until closed by the client later or the connection is timed out. 

*Note:* Please refer to nginx-light for the expected behaviours of SWS.
