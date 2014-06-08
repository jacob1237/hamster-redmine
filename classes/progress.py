#!/usr/bin/evn python
# encoding: utf-8

import sys


class ProgressBar(object):
    """
    Simple progress bar class
    """

    progress = 0.00

    def __init__(self, width=20,
                         bar="\r[%s%s] %d%%"):
        self.width = width
        self.bar = bar

    def __add__(self, value):
        self.progress += value
        return self

    def draw(self):
        fill = int(self.width / 100.0 * self.progress)

        sys.stdout.write(
            self.bar % (('#' * fill), '.' * (self.width - fill), \
                        self.progress,))
        sys.stdout.flush()
