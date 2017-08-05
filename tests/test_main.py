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
import tempfile
import io

import pytest
from gi.repository import Gio

from giofile import open as gopen


@pytest.yield_fixture
def gfile():
    fd, name = tempfile.mkstemp()
    os.close(fd)
    f = Gio.File.new_for_path(name)
    try:
        yield f
    finally:
        os.unlink(name)


def test_seek(gfile):
    with gopen(gfile, "rb") as f:
        assert f.seekable()
        assert f.seek(0, 0) == 0


def test_tell(gfile):
    with gopen(gfile, "rb") as f:
        assert f.seek(1, 0) == f.tell()


def test_truncate(gfile):
    with gopen(gfile, "r+b") as f:
        with open(f.name, "wb") as h:
            h.write(b"foo")
        assert f.seek(0, 2) == 3
        f.seek(0, 0)
        f.truncate()
        assert f.seek(0, 2) == 0


def test_close(gfile):
    with gopen(gfile, "r+b") as f:
        assert not f.closed
        f.close()
        assert f.closed
        f.close()

    with gopen(gfile, "r+b") as f:
        pass
    assert f.closed


def test_readable_writable(gfile):
    with gopen(gfile, "rb") as f:
        assert f.readable()
        assert not f.writable()

    with gopen(gfile, "r+b") as f:
        assert f.readable()
        assert f.writable()


def test_fileno(gfile):
    with gopen(gfile, "rb") as f:
        assert isinstance(f.fileno(), int)


def test_read_write(gfile):
    with gopen(gfile, "r+b") as f:
        with open(f.name, "wb") as h:
            h.write(b"foo")
        assert f.read(1) == b"f"
        assert f.read() == b"oo"
        assert f.write(b"bar") == 3


def test_flush_closed(gfile):
    with gopen(gfile, "r+b") as f:
        pass
    with pytest.raises(ValueError):
        f.flush()


def test_isatty(gfile):
    with gopen(gfile, "r+b") as f:
        assert not f.isatty()


def test_readline(gfile):
    with gopen(gfile, "r+b") as f:
        with open(f.name, "wb") as h:
            h.write(b"foo\nbar")
        assert f.readline() == b"foo\n"
        assert f.readline() == b"bar"
        assert f.readline() == b""


def test_iter(gfile):
    with gopen(gfile, "r+b") as f:
        with open(f.name, "wb") as h:
            h.write(b"foo\nbar")
        assert [l for l in f] == [b"foo\n", b"bar"]


def test_readinto(gfile):
    data = b"x" * (io.DEFAULT_BUFFER_SIZE * 10)
    with gopen(gfile, "r+b") as f:
        with open(f.name, "wb") as h:
            h.write(data)

        assert f.read() == data
        f.seek(0)
        buf = bytearray(len(data))
        f.readinto(buf)
        assert buf == data


def test_buffered_reader(gfile):
    with gopen(gfile, "rb") as f:
        with open(f.name, "wb") as h:
            h.write(b"foo")
        assert f.peek(3) == b"foo"
        assert f.tell() == 0
        f.read1(10)


def test_buffered_writer(gfile):
    cancel = Gio.Cancellable.new()
    with gopen(gfile, "r+b", cancellable=cancel) as f:
        with open(f.name, "wb") as h:
            h.write(b"foo")
        with io.BufferedWriter(f) as b:
            b.write(b"x")
            b.flush()
            f.seek(0)
            assert f.read() == b"xoo"


def test_http():
    gfile = Gio.File.new_for_uri(
        "http://people.xiph.org/~giles/2012/opus/ehren-paper_lights-96.opus")
    with pytest.raises(IOError):
        gopen(gfile, "r+b")

    with gopen(gfile, "rb") as f:
        assert f.name == "ehren-paper_lights-96.opus"
        with pytest.raises(IOError):
            f.fileno()


def test_kwargs(gfile):
    with pytest.raises(TypeError):
        gopen(gfile, foo=1)


def test_text_mode(gfile):
    with gopen(gfile, "r") as f:
        with open(f.name, "wb") as h:
            h.write(b"foo")
        assert f.read() == u"foo"


def test_line_buffering(gfile):
    with gopen(gfile, "r") as f:
        assert not f.line_buffering

    with gopen(gfile, "r", buffering=1) as f:
        assert f.line_buffering


def test_invalid_buffering(gfile):
    with pytest.raises(ValueError):
        gopen(gfile, "r", buffering=0)

    with pytest.raises(ValueError):
        gopen(gfile, "rb", buffering=1)
