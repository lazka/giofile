*******
giofile
*******

Opens a Gio.File as a Python file object

.. code:: python

    def open(file, mode="r", buffering=-1, encoding=None, errors=None,
             newline=None, cancellable=None):
        """
        Like io.open() but takes a Gio.File instead of a filename.

        The only modes supported are r/rw/rb/r+b
        Takes a cancellable kwarg for passing a Gio.Cancellable().
        Cancelling it will abort any ongoing blocking operation.

        Returns a io.IOBase instance.
        """

.. image:: https://travis-ci.org/lazka/giofile.svg?branch=master
    :target: https://travis-ci.org/lazka/giofile

Example
=======

.. code:: python

    import mutagen
    import giofile
    from gi.repository import Gio

    gio_file = Gio.File.new_for_uri(
        "http://people.xiph.org/~giles/2012/opus/ehren-paper_lights-96.opus")

    cancellable = Gio.Cancellable.new()
    with giofile.open(gio_file, "rb", cancellable=cancellable) as gfile:
        print(mutagen.File(gfile).pprint())

.. code:: sh

    $ python example.py
    Ogg Opus, 228.11 seconds (audio/ogg)
    ENCODER=opusenc from opus-tools 0.1.5
    artist=Ehren Starks
    title=Paper Lights
    album=Lines Build Walls
    date=2005-09-05
    copyright=Copyright 2005 Ehren Starks
    license=http://creativecommons.org/licenses/by-nc-sa/1.0/
    organization=magnatune.com
