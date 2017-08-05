# -*- coding: utf-8 -*-
# Copyright 2017 Christoph Reiter
#
# Permission is hereby granted, free of charge, to any person obtaining
# a copy of this software and associated documentation files (the
# "Software"), to deal in the Software without restriction, including
# without limitation the rights to use, copy, modify, merge, publish,
# distribute, sublicense, and/or sell copies of the Software, and to
# permit persons to whom the Software is furnished to do so, subject to
# the following conditions:
#
# The above copyright notice and this permission notice shall be included
# in all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND,
# EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF
# MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT.
# IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY
# CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT,
# TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE
# SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.

import os
import io

from gi.repository import GLib, Gio


def reraise(func):
    def wrap(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except GLib.Error as e:
            raise IOError(e.message)
    return wrap


class GioFile(io.RawIOBase):

    @reraise
    def __init__(self, gfile, writable, cancellable):
        super(GioFile, self).__init__()

        self._file = gfile
        self._cancellable = cancellable
        if writable:
            self._iostream = self._file.open_readwrite(cancellable)
            self._istream = self._iostream.get_input_stream()
            self._ostream = self._iostream.get_output_stream()
        else:
            self._iostream = self._file.read(cancellable)
            self._istream = self._iostream
            self._ostream = None

    @reraise
    def close(self):
        if not self._iostream.is_closed():
            self._iostream.close(self._cancellable)
        if not self._istream.is_closed():
            self._istream.close(self._cancellable)
        if self._ostream:
            if not self._ostream.is_closed():
                self._ostream.close(self._cancellable)

    @property
    @reraise
    def closed(self):
        return self._iostream.is_closed()

    @reraise
    def tell(self):
        if self._ostream:
            return self._ostream.tell()
        return self._istream.tell()

    @reraise
    def seekable(self):
        return self._iostream.can_seek()

    @reraise
    def readinto(self, b):
        size = len(b)
        data = True
        offset = 0
        while offset < size and data:
            data = self._istream.read_bytes(
                size - offset, self._cancellable).get_data()
            b[offset:offset + len(data)] = data
            offset += len(data)
        return offset

    @reraise
    def seek(self, offset, whence=0):
        whence = {1: 0, 0: 1, 2: 2}[whence]
        self._iostream.seek(offset, whence, self._cancellable)
        return self.tell()

    @property
    def name(self):
        path = self._file.get_path()
        if path is not None:
            return path

        try:
            file_info = self._file.query_info(
                Gio.FILE_ATTRIBUTE_STANDARD_DISPLAY_NAME,
                Gio.FileQueryInfoFlags.NONE,
                self._cancellable)
        except GLib.Error:
            display_name = None
        else:
            display_name = file_info.get_display_name()

        if display_name is not None:
            return display_name

        uri = self._file.get_uri()
        if uri is not None:
            return uri

        return ""

    @reraise
    def write(self, data):
        if not self._ostream:
            raise IOError("read only")
        if isinstance(data, memoryview):
            data = bytearray(data)
        return self._ostream.write(data, self._cancellable)

    @reraise
    def truncate(self, size=None):
        if size is None:
            size = self.tell()
        self._iostream.truncate(size, self._cancellable)

    @reraise
    def flush(self):
        if self._ostream:
            self._ostream.flush(self._cancellable)

    def fileno(self):
        try:
            return self._istream.get_fd()
        except AttributeError:
            raise IOError("No fileno available")

    def isatty(self):
        try:
            return os.isatty(self.fileno())
        except (OSError, IOError):
            return False

    def readable(self):
        return True

    def writable(self):
        return self._ostream is not None


def open(file, mode="r", buffering=-1, encoding=None, errors=None,
         newline=None, **kwargs):
    """
    Like io.open() but takes a Gio.File instead of a filename.

    The only modes supported are r/rw/rb/r+b
    Takes a cancellable kwarg for passing a Gio.Cancellable().
    Cancelling it will abort any ongoing blocking operation.

    Returns a io.IOBase instance.
    """

    cancellable = kwargs.pop("cancellable", None)
    if kwargs:
        raise TypeError("Unhandled keyword args: %r" % sorted(kwargs.keys()))

    if mode == "r":
        writable = False
        text = True
    elif mode == "w":
        raise ValueError("write only not supported, use rw")
    elif mode == "rw":
        writable = True
        text = True
    elif mode == "rb":
        writable = False
        text = False
    elif mode == "wb":
        raise ValueError("write only not supported, use r+b")
    elif mode == "r+b":
        writable = True
        text = False
    else:
        raise ValueError("Mode %r not supported, only r/rw/rb/r+b" % mode)

    if buffering == 0 and text:
        raise ValueError("Without buffer only allowed in binary mode")
    if buffering == 1 and not text:
        raise ValueError("Line buffering only allowed in text mode")

    f = GioFile(file, writable, cancellable)

    try:
        line_buffering = (buffering == 1) or (text and f.isatty())
        buffer_size = buffering if buffering > 1 else io.DEFAULT_BUFFER_SIZE
        buffered = buffering != 0
        buffer_wrapper = io.BufferedRandom if writable else io.BufferedReader

        if buffered:
            f = buffer_wrapper(f, buffer_size)

        if text:
            assert buffered
            f = io.TextIOWrapper(
                f, encoding, errors, newline, line_buffering=line_buffering)
    except Exception:
        f.close()
        raise

    return f
