# -*- coding: utf-8 -*-
import json
import socket
import sys
import os
import time
import platform
import threading
import model


BUFFER_SIZE = 2 ** 10
CLEAR_COMMAND = ''
CLOSING = 'Application closing...'
CONNECTION_ABORTED = 'Connection aborted'
CONNECTED_PATTERN = 'Client connected: {}:{}'
ERROR_ARGUMENTS = 'Provide port number as the first command line argument'
ERROR_OCCURRED = 'Error Occurred'
INVALID_TURN = '{} tried to commit invalid turn.'
MAX_PLAYERS = 10
RUNNING = 'Server is running...'


class Server(object):

    def __init__(self, argv):
        self.clients = {}
        self.listen_thread = None
        self.print_thread = None
        self.port = None
        self.sock = None
        self.parse_args(argv)
        self.gamefield = model.GameField()
        self.lock = threading.Lock()

    def log_in(self, client):
        try:
            username = json.loads(self.receive(client))
        except (ConnectionAbortedError, ConnectionResetError):
            print(CONNECTION_ABORTED)
            return False
        if username in self.gamefield.players:
            return False
        else:
            self.clients[client] = username
            self.gamefield.players.append(username)
            fork = model.Fork(occupied_by=None)
            self.gamefield.forks.append(fork)
            return True

    def remove_player(self, client):
        username = self.clients[client]
        idx = self.gamefield.players.index(username)
        self.gamefield.players.pop(idx)
        self.gamefield.forks.pop(idx)

    def validate_turn(self, client, turn):
        if self.clients[client] == turn.username:
            idx = self.gamefield.players.index(turn.username)
            if turn.fork_pos == -1:
                fork = self.gamefield.forks[idx - 1]
            elif turn.fork_pos == 1:
                fork = self.gamefield.forks[idx]
            elif turn.fork_pos == 0:
                return True
            else:
                return False
            if fork.occupied_by is None:
                fork.occupied_by = turn.username
                return True
            elif fork.occupied_by == turn.username:
                fork.occupied_by = None
                return True
            else:
                return False
        else:
            return False

    def listen(self):
        self.sock.listen(MAX_PLAYERS)
        while True:
            try:
                client, address = self.sock.accept()
            except OSError:
                print(CONNECTION_ABORTED)
                return
            print(CONNECTED_PATTERN.format(*address))
            logged_in = self.log_in(client)
            # send login status to client
            try:
                client.sendall(model.marshal_primitive(logged_in))
            except (ConnectionAbortedError, ConnectionResetError):
                self.remove_player(client)
                print(CONNECTION_ABORTED)
            if logged_in:
                threading.Thread(target=self.handle, args=(client,)).start()

    def handle(self, client):
        try:
            self.broadcast(self.gamefield)
        except (ConnectionAbortedError, ConnectionResetError):
            self.remove_player(client)
            print(CONNECTION_ABORTED)
        while True:
            try:
                turn = model.Turn(**json.loads(self.receive(client)))
            except (ConnectionAbortedError, ConnectionResetError):
                self.remove_player(client)
                print(CONNECTION_ABORTED)
                continue
            self.lock.acquire()
            turn_valid = self.validate_turn(client, turn)
            self.lock.release()
            if turn_valid:
                self.broadcast(self.gamefield)

    def broadcast(self, gamefield):
        for client in self.clients:
            client.sendall(gamefield.marshal())

    def receive(self, client):
        buffer = ''
        while not buffer.endswith(model.END_CHARACTER):
            buffer += client.recv(BUFFER_SIZE).decode(model.TARGET_ENCODING)
        return buffer[:-1]

    def run(self):
        print(RUNNING)
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock.bind(('', self.port))
        self.listen_thread = threading.Thread(target=self.listen)
        self.listen_thread.start()
        self.print_thread = threading.Thread(target=self.print_gamefield)
        self.print_thread.start()

    def print_gamefield(self):
        while True:
            print(str(self.gamefield))
            time.sleep(1)

    def parse_args(self, argv):
        if len(argv) != 2:
            raise RuntimeError(ERROR_ARGUMENTS)
        try:
            self.port = int(argv[1])
        except ValueError:
            raise RuntimeError(ERROR_ARGUMENTS)

    def exit(self):
        self.sock.close()
        for client in self.clients:
            client.close()
        print(CLOSING)


if __name__ == '__main__':
    if platform.system() == 'Windows':
        os.system('color')
        CLEAR_COMMAND = 'cls'
    else:
        CLEAR_COMMAND = 'clear'
    try:
        Server(sys.argv).run()
    except RuntimeError as error:
        print(ERROR_OCCURRED)
        print(str(error))