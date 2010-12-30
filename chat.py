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
                conn.send("Welcome %s!\n" % name)
                list_commands(conn)
                list_users(conn)
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
    for to_name, conn in users.items():
        if to_name != name:
            try:
                conn.send(message + "\n")
            except socket.error:
                pass


def quit(conn):
    """
    Disconnect a connection.
    """
    conn.close()


def list_users(conn):
    """
    Send the list of users to a connection.
    """
    conn.send("Current users are: %s\n" % ", ".join(users.keys()))


def list_commands(conn):
    """
    Send the list of commands to a connection.
    """
    conn.send("Available commands are: %s\n" % " ".join(commands.keys()))


def serve(host, port):
    """
    Main function - set up server socket and run main event loop.
    """
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server.setblocking(False)
    server.bind((host, port))
    server.listen(1)
    print "Listening on %s:%s" % server.getsockname()
    # Main event loop.
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
                    # Empty string is given on disconnect, close connection.
                    conn.close()
                else:
                    # Handle command if given, otherwise broadcast message.
                    message = message.strip()
                    try:
                        command = commands[message]
                    except KeyError:
                        broadcast(name, message)
                    else:
                        command(conn)
                # Check for disconnected users and remove them.
                try:
                    conn.send("")
                except socket.error:
                    del users[name]
                    broadcast(name, action="leaves")
            time.sleep(.1)
        except (SystemExit, KeyboardInterrupt):
            print "shutdown?"
            broadcast(action="shutting down")
            for conn in users.values():
                conn.close()
            break


def client(host, port, name):
    """
    Connects to the given host and port and joins the chat with the 
    given username.
    """
    client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    client.setblocking(False)
    # Reading console input and sending to the server must run 
    # in a separate thread so as not to block.
    def handle_input():
        while True:
            client.send(raw_input())
    # Connect to the server.
    retries = 10
    while True:
        try:
            client.connect((host, port))
            break
        except socket.error:
            retries -= 1
            if retries > 0:
                time.sleep(1)
            else:
                print "Couldn't connect to %s:%s" % client.getsockname()
                return
    # Read from connection.
    name_sent = False
    while True:
        try:
            try:
                message = client.recv(1024).strip()
                if not name_sent:
                    # Set the username on first response.
                    name_sent = True
                    client.send(name)
                    thread.start_new_thread(handle_input, ())
                else:
                    print message
            except socket.error:
                time.sleep(.1)
        except (SystemExit, KeyboardInterrupt):
            client.close()
            break


# user name/connection mapping for all users.
users = {}

# command name/handler mapping for commands.
commands = {
    "!quit": quit,
    "!users": list_users,
    "!commands": list_commands,
}


if __name__ == "__main__":
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
    # Run server.
    thread.start_new_thread(serve, (host, port))
    time.sleep(1)
    client(host, port, raw_input("Please enter your name: "))
