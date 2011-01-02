#!/usr/bin/env python

import functools
import optparse
import socket
import thread
import threading
import time


__version__ = "0.1"


def nonblocking(func):
    """
    Decorator that runs the decorated func in a separate thread 
    when called.
    """
    @functools.wraps(func)
    def wrapper(*args):
        thread.start_new_thread(func, args)
    return wrapper

    
class StoppableThread(threading.Thread):
    """
    Thread class that runs a main() method until the stop() method 
    is called.
    """
    
    def stop(self):
        """
        Stops the main event loop.
        """
        self.running = False

    def main(self):
        """
        Main method to be overridden by subclass that runs each 
        event loop iteration.
        """
        pass

    def end(self):
        """
        Called once the thread had been stopped and the final 
        iteration of main() has run.
        """
        pass
        
    def run(self):
        """
        Run main method until stop() is called.
        """
        self.running = True
        while self.running:
            self.main()
            time.sleep(.1)
        self.end()


class Server(StoppableThread):
    """
    Chat server.
    """
    
    def __init__(self, host, port, shutdown_delay=5):
        """
        Set up the server socket.
        """
        super(Server, self).__init__()
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.socket.setblocking(False)
        self.socket.bind((host, port))
        self.socket.listen(1)
        self.shutdown_delay = shutdown_delay
        self.users = {}
        self.commands = {
            "!quit": "quit",
            "!users": "list_users",
            "!commands": "list_commands",
        }

    def main(self):
        """
        Main event loop iteration.
        """
        # Accept new connections.
        while True:
            try:
                conn, addr = self.socket.accept()
            except socket.error:
                break
            self.accept(conn)
        # Read from connections.
        for name, conn in self.users.items():
            try:
                message = conn.recv(1024)
            except socket.error:
                continue
            if not message:
                # Empty string is given on disconnect,
                # close connection.
                conn.close()
            else:
                # Handle command if given, otherwise 
                # broadcast message.
                message = message.strip()
                try:
                    command = self.commands[message]
                except KeyError:
                    self.broadcast(name, message)
                else:
                    getattr(self, command)(conn)
            # Check for disconnected users and remove them.
            try:
                conn.send("")
            except socket.error:
                del self.users[name]
                self.broadcast(name, action="leaves")
    
    def end(self):
        """
        Send a shutdown message to all users and close their 
        connections.
        """
        message = "shutting down in %s seconds" % self.shutdown_delay
        self.broadcast(action=message)
        time.sleep(self.shutdown_delay)
        for conn in self.users.values():
            conn.close()
            
    @nonblocking
    def accept(self, conn):
        """
        Call the inner func in a thread so as not to block. Wait for a 
        name to be entered from the given connection. Once a name is 
        entered, set the connection to non-blocking and add the user to 
        the users dict.
        """
        while True:
            conn.send("Please enter your name: ")
            try:
                name = conn.recv(1024).strip()
            except socket.error:
                continue
            if name in self.users.keys():
                conn.send("Name entered is already in use.\n")
            elif name:
                conn.setblocking(False)
                self.users[name] = conn
                conn.send("Welcome %s!\n" % name)
                self.list_commands(conn)
                self.list_users(conn)
                self.broadcast(name, action="joins")
                break

    def broadcast(self, name="", message=None, action=None):
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
        for to_name, conn in self.users.items():
            if to_name != name:
                try:
                    conn.send(message + "\n")
                except socket.error:
                    pass

    def quit(self, conn):
        """
        Disconnect a connection.
        """
        conn.close()

    def list_users(self, conn):
        """
        Send the list of users to a connection.
        """
        users = sorted(self.users.keys())
        conn.send("Current users are: %s\n" % ", ".join(users))

    def list_commands(self, conn):
        """
        Send the list of commands to a connection.
        """
        commands = sorted(self.commands.keys())
        conn.send("Available commands are: %s\n" % " ".join(commands))


class Client(StoppableThread):
    """
    Chat client.
    """
    
    def __init__(self, host, port, name, connect_retries=10):
        """
        Set up the client socket and connect to the server..
        """
        super(Client, self).__init__()
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket.setblocking(False)
        self.name = name
        self.name_sent = False
        while True:
            try:
                self.socket.connect((host, port))
                break
            except socket.error:
                connect_retries -= 1
                if connect_retries > 0:
                    time.sleep(1)
                else:
                    print "Couldn't connect to %s:%s" % (host, port)
                    return

    def main(self):
        """
        Main event loop iteration - read responses from the server. 
        On first response, send the specified username.
        """
        try:
            message = self.socket.recv(1024)
        except socket.error:
            time.sleep(.1)
        else:
            if not message:
                self.stop()
            else:
                message = message.strip()
                if not self.name_sent:
                    # Set the username on first response.
                    self.name_sent = True
                    self.socket.send(self.name)
                    self.handle_input()
                else:
                    print message
        # Handle disconnection.
        try:
            self.socket.send("")
        except socket.error:
            self.stop()

    def end(self):
        """
        Close socket on end.
        """
        self.socket.close()

    @nonblocking
    def handle_input(self):
        """
        Reads input from the terminal and sends it as a message.
        """
        while True:
            try:
                self.socket.send(raw_input())
            except socket.error:
                # Connection closed.
                break


def main():
    """
    Start client and/or server based on command line options 
    and run them until exit.
    """

    # Get command line options.
    parser = optparse.OptionParser(usage="usage: %prog [options]")
    parser.add_option("-b", "--bind", dest="bind", help="Address for the "
                      "chat server to, in the format host:port")
    parser.add_option("-c", "--client-only", dest="client_only", 
                      action="store_true", default=False, 
                      help="Only run the client")
    parser.add_option("-s", "--server-only", dest="server_only", 
                      action="store_true", default=False, 
                      help="Only run the server")
    options, args = parser.parse_args()
    try:
        host, port = options.bind.split(":")
        port = int(port)
    except AttributeError:
        parser.error("Address not specified")
    except ValueError:
        parser.error("Address not in the format host:port")
    if options.client_only and options.server_only:
        parser.error("Cannot specify client-only and server-only")

    # Run server and client.
    if not options.client_only:
        server = Server(host, port)
        server.start()
        print "Listening on %s:%s" % server.socket.getsockname()
        if not options.server_only:
            time.sleep(1)
    if not options.server_only:
        name = raw_input("Please enter your name: ")
        client = Client(host, port, name)
        client.start()

    # Wait for exit.
    while True:
        try:
            time.sleep(.1)
        except (SystemExit, KeyboardInterrupt):
            break
    if not options.server_only:
        client.stop()
    if not options.client_only:
        server.stop()


if __name__ == "__main__":
    main()
