#!/usr/bin/env python

import socket
import thread
import time


HOST = ""
PORT = 4004


def accept(conn):
    """
    Call the inner func in a thread so as not to block. Wait for a 
    name to be entered from the given connection. Once a name is 
    entered, set the connection to non-blocking and add the user to 
    the users dict.
    """
    def threaded():
        while True:
            conn.send("Please enter your name: ")
            try:
                name = conn.recv(1024).strip()
            except socket.error:
                continue
            if name in users.keys():
                conn.send("Name entered is already in use.\n")
            elif name:
                conn.setblocking(False)
                users[name] = conn
                broadcast(name, action="joins")
                break
    thread.start_new_thread(threaded)


def broadcast(name="", message=None, action=None):
    """
    Send a message to all users from the given name. If no name specified, 
    the message is from the server. If no message is specified and an action 
    is given, use the action as the message without a colon prefix to 
    signify it isn't a message.
    """
    if message is None:
        message = "%s %s" % (name, action)
    else:
        message = "%s: %s" % (name, message)
    print message
    for to_name, conn in users.items():
        if to_name != name:
            try:
                conn.send(message + "\n")
            except socket.error:
                pass


# Set up the server socket.
server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
server.setblocking(False)
server.bind((HOST, PORT))
server.listen(1)
print "Listening on %s" % ("%s:%s" % server.getsockname())

# Main event loop.
users = {}
while True:
    try:
        # Accept new connections.
        while True:
            try:
                conn, addr = server.accept()
            except socket.error:
                break
            accept(conn)
        # Read from connections.
        for name, conn in users.items():
            try:
                message = conn.recv(1024)
            except socket.error:
                continue
            if not message:
                # Empty string is given on disconnect.
                del users[name]
                broadcast(name, action="leaves")
            else:
                broadcast(name, message.strip())
        time.sleep(.1)
    except (SystemExit, KeyboardInterrupt):
        broadcast(action="shutting down")
        break
