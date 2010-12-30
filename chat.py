#!/usr/bin/env python

import optparse
import socket
import thread
import threading
import time


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
        self.server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.server.setblocking(False)
        self.server.bind((host, port))
        self.server.listen(1)
        print "Listening on %s:%s" % self.server.getsockname()
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
                conn, addr = self.server.accept()
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
            
    def accept(self, conn):
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
        thread.start_new_thread(threaded, ())

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
            # Handle disconnection.
            try:
                client.send("")
            except socket.error:
                break
        except (SystemExit, KeyboardInterrupt):
            break
    client.close()


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
    server = Server(host, port)
    server.start()
    time.sleep(1)
    client(host, port, raw_input("Please enter your name: "))
    server.stop()
