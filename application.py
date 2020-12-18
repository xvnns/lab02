# -*- coding: utf-8 -*-
import json
import socket
import threading
import time
import platform
import os
import model


BUFFER_SIZE = 2 ** 10
CONNECTION_ERROR = "Could not connect to server"
CLEAR_COMMAND = ''
LOGIN_ERROR = 'Could not log in! Username is already taken or server error occurred.'


class Application(object):

    def __init__(self, args):
        self.args = args
        self.closing = False
        self.host = None
        self.port = None
        self.receive_worker = None
        self.sock = None
        self.username = None
        self.gamefield = None
        global CLEAR_COMMAND
        if platform.system() == 'Windows':
            CLEAR_COMMAND = 'cls'
        else:
            CLEAR_COMMAND = 'clear'

    def gameloop(self):
        while True:
            os.system(CLEAR_COMMAND)
            print(f'Username: {self.username}')
            print('\n')
            print(str(self.gamefield))
            print('\n\n\n')
            print('What fork is to be wielded, Ay there\'s the point,')
            print('The left, the right one, is that all? Aye all...')
            print()
            print('Your choice (l/r/o): ', end='')
            choice = input()
            if choice == 'l':
                fork_pos = -1
            elif choice == 'r':
                fork_pos = 1
            elif choice == 'o':
                fork_pos = 0
            else:
                continue
            turn = model.Turn(username=self.username, fork_pos=fork_pos)
            self.send(turn)

    def input_fields(self):
        while True:
            self.username = input('Username: ')
            if self.username is not None:
                break
        while True:
            self.host = input('Server host: ')
            if self.host is not None:
                break
        while True:
            self.port = int(input('Server port: '))
            if self.port is not None:
                break

    def execute(self):
        self.input_fields()
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        # connect to server
        try:
            self.sock.connect((self.host, self.port))
        except (socket.error, OverflowError):
            print(CONNECTION_ERROR)
            return
        # log in
        try:
            self.sock.sendall(model.marshal_primitive(self.username))
            logged_in = json.loads(self.receive_all())
        except (ConnectionAbortedError, ConnectionResetError):
            if not self.closing:
                print(CONNECTION_ERROR)
            return
        # listen for server and start game loop
        if logged_in:
            self.receive_worker = threading.Thread(target=self.receive)
            self.receive_worker.start()
            self.gameloop()
        else:
            print(LOGIN_ERROR)

    def receive(self):
        while True:
            try:
                gamefield = model.GameField.from_json(json.loads(self.receive_all()))
            except (ConnectionAbortedError, ConnectionResetError):
                if not self.closing:
                    print(CONNECTION_ERROR)
                return
            self.gamefield = gamefield

    def receive_all(self):
        buffer = ''
        while not buffer.endswith(model.END_CHARACTER):
            buffer += self.sock.recv(BUFFER_SIZE).decode(model.TARGET_ENCODING)
        return buffer[:-1]

    def send(self, turn):
        try:
            self.sock.sendall(turn.marshal())
        except (ConnectionAbortedError, ConnectionResetError):
            if not self.closing:
                print(CONNECTION_ERROR)

    def exit(self):
        self.closing = True
        self.sock.close()
