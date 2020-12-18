# -*- coding: utf-8 -*-

import json
from enum import Enum

END_CHARACTER = '\0'
MESSAGE_PATTERN = '{} wants to occupy {} fork'
TARGET_ENCODING = 'utf-8'
SPACE = '  '
'\033[m'
RED = '\033[31m'
GREEN = '\033[32m'
BLUE = '\033[34m'
ENDC = '\033[0m'


def marshal_primitive(obj):
    return (json.dumps(obj) + END_CHARACTER).encode(TARGET_ENCODING)


class Turn:

    def __init__(self, **kwargs):
        self.username = None
        self.fork_pos = None
        self.__dict__.update(kwargs)

    def __str__(self):
        if self.fork_pos == -1:
            fork_pos = 'left'
        elif self.fork_pos == 1:
            fork_pos = 'right'
        elif self.fork_pos == 0:
            fork_pos = 'no'
        else:
            raise ValueError('\'fork_pos\' must be either -1 or 1.')
        return MESSAGE_PATTERN.format(self.username, fork_pos)

    def marshal(self):
        return (json.dumps(self.__dict__) + END_CHARACTER).encode(TARGET_ENCODING)


class GameField:

    def __init__(self, **kwargs):
        self.forks = []
        self.players = []
        self.__dict__.update(kwargs)

    def __str__(self):
        s = '|' + SPACE
        for i in range(len(self.players)):
            if len(self.forks) == 0:
                break
            # username
            if self.forks[i - 1].occupied_by == self.forks[i].occupied_by == self.players[i]:
                s += BLUE + self.players[i] + ENDC
            else:
                s += self.players[i]
            s += SPACE
            # fork
            if self.forks[i].occupied_by is not None:
                s += RED + 'ш' + ENDC
            else:
                s += GREEN + 'ш' + ENDC
            s += SPACE
        s += '|'
        return s

    def marshal(self):
        return (json.dumps(self, default=lambda o: o.__dict__) + END_CHARACTER).encode(TARGET_ENCODING)

    @classmethod
    def from_json(cls, data: dict):
        forks = list(map(Fork.from_json, data['forks']))
        return cls(forks=forks, players=data['players'])


class Fork:

    def __init__(self, **kwargs):
        self.occupied_by = None
        self.__dict__.update(kwargs)

    @classmethod
    def from_json(cls, data: dict):
        return cls(**data)
