# -*- coding: utf-8 -*-
import sys
import os
import platform
import application


CLEAR_COMMAND = ''


def main(args):
    app = application.Application(args)
    app.execute()


if __name__ == '__main__':
    if platform.system() == 'Windows':
        os.system('color')
    main(sys.argv)
