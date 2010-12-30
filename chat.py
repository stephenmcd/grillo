#!/usr/bin/env python

import optparse
import socket
import thread
import time


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
    thread.start_new_thread(threaded, ())


def broadcast(name="", message=None, action=None):
    """
    Send a message to all users from the given name. If no name specified, 
    the message is from the server. If no message is specified and an action 
    is given, use the action as the message without a colon prefix to 
    signify it isn't a message.
    """
    timestamp = time.strftime("[%I:%M:%S]")
    if message is None:
        message = "%s %s %s" % (timestamp, name, action)
    else:
        message = "%s %s: %s" % (timestamp, name, message)
    print message
    for to_name, conn in users.items():
        if to_name != name:
            try:
                conn.send(message + "\n")
            except socket.error:
                pass

# Get host and port from command line arg.
parser = optparse.OptionParser(usage="usage: %prog -b host:port")
parser.add_option("-b", "--bind", dest="bind", help="Address for the "
                  "chat server to, in the format host:port")
options, args = parser.parse_args()
try:
    host, port = options.bind.split(":")
    port = int(port)
except AttributeError:
    parser.error("Address not specified")
except ValueError:
    parser.error("Address not in the format host:port")

# Mapping of commands.
commands = {
    "!quit": lambda conn: conn.close(),
}

# Set up the server socket.
server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
server.setblocking(False)
server.bind((host, port))
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
                # Handle command if given, otherwise broadcast message.
                message = message.strip()
                try:
                    command = commands[message]
                except KeyError:
                    broadcast(name, message)
                else:
                    command(conn)
        time.sleep(.1)
    except (SystemExit, KeyboardInterrupt):
        broadcast(action="shutting down")
        for conn in users.values():
            conn.close()
        break
