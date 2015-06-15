# Comments marked with a * are verbatim from the article or source. See README

# Note: Python has a SocketServer.TCPServer class that would make this easier.
# To stay closer to the original intention though, we are sticking with socket.
from socket import socket, AF_INET, SOCK_STREAM
from urlparse import urlparse
from urllib import url2pathname
import os.path

#*Files will be served from this directory
WEB_ROOT = './public'

#*Map extensions to their content type
CONTENT_TYPE_MAPPING = {
    '.html': 'text/html',
    '.txt':  'text/plain',
    '.png':  'image/png',
    '.jpg':  'image/jpeg'
    }

#*Treat as binary data if content type cannot be found
DEFAULT_CONTENT_TYPE = 'application/octet-stream'

#*This helper function parses the extension of the requested file and then
# looks up its content type.
def content_type(path):
    ext = os.path.splitext(path)[1]
    return CONTENT_TYPE_MAPPING.get(ext, DEFAULT_CONTENT_TYPE)

#*This helper function parses the Request-Line and generates a path to a file
# on the server.
def requested_file(request_line):
    request_uri = request_line.split(" ")[1]
    # urlparse will provide us the path, url2pathname will decode characters
    # and give us a path our local filesystem speaks (e.g. forward slashes on
    # nix and backslashes on Windows).
    path = url2pathname(urlparse(request_uri).path)

    clean = []

    parts = path.split("/")
    for part in parts:
        #*skip any empty or current directory (".") path components
        if not part or part == '.':
            continue

        #*If the path component goes up one directory (".."), remove the last
        # clean component. Otherwise, add the component to the Array of clean
        # components.
        if part == '..':
            clean.pop()
        else:
            clean.append(part)

    return os.path.join(WEB_ROOT, *clean)

server = socket()

# bind() takes an address tuple consisting of host and port.
# This server will listen on localhost:2345 for incoming connections.
server.bind(('localhost', 2345))

# We're only going to queue up to one connection. If other connections are
# made while the server is processing another, it will not be "queued."
server.listen(1)

# As mentioned, we're only going to process one connection at a time, but we'll
# keep doing this forever.
while True:
    try:
        # Wait until a client connects. accept() gives us the address connecting to
        # our socket server, as well as a socket object for this one connection.
        connection, address = server.accept()

        # Receive up to 1024 bytes from the socket that we just accepted a
        # connection from.
        request = connection.recv(1024)
    except KeyboardInterrupt:
        # When we terminate with Ctrl+C we need to close our server socket. If we
        # don't, the operating system will think the address we bound to (from the
        # bind() call) is still in use.
        #
        # The reason why the try/except block is _here_ is because the calls to
        # accept() and recv() will "block" the program from continuing until
        # they're complete. Thus without the try/except, any interrupt would be
        # ignored.
        connection.close()
        break

    request_line = request.split("\n")[0]

    # Print just the first line of the request (the Request-Line)
    print '{}: {}'.format(address, request_line)

    path = requested_file(request_line)
    if os.path.isdir(path):
        path = os.path.join(path, 'index.html')

    if os.path.isfile(path):
        with open(path, 'rb') as file:
            contents = file.read()
            connection.sendall("HTTP/1.1 200 OK\r\n" +
                               "Connection-Type: {}\r\n".format(content_type(path)) +
                               "Content-Length: {}\r\n".format(len(contents)) +
                               "Connection: close\r\n")
            connection.sendall("\r\n")
            connection.sendall(contents)
    else:
        message = "File not found\n"

        #*respond with a 404 error code to indicate the file does not exist
        connection.sendall("HTTP/1.1 404 Not Found\r\n" +
                           "Connection-Type: text/plain\r\n" +
                           "Content-Length: {}\r\n".format(len(message)) +
                           "Connection: close\r\n")
        connection.sendall("\r\n")
        connection.sendall(message)

    # Close the socket we have a connection with.
    connection.close()

print 'Closing socket server.'
server.close()
