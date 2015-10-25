# -*- coding: utf-8 -*-
# #
# #    Copyright (C) 2005 manatlan manatlan[at]gmail(dot)com
# #
# # This program is free software; you can redistribute it and/or modify
# # it under the terms of the GNU General Public License as published
# # by the Free Software Foundation; version 2 only.
# #
# # This program is distributed in the hope that it will be useful,
# # but WITHOUT ANY WARRANTY; without even the implied warranty of
# # MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# # GNU General Public License for more details.
# #

from gi.repository import Gtk, GObject, GdkPixbuf
from subprocess import Popen, PIPE


def colorToString(color):
    """
    Converts a gtk.gdk color to a string
    (fix for windows not having the to_string member function)"""
    return "#%x%x%x" % (color.red, color.blue, color.green)

##############################################################################
##############################################################################
##############################################################################

from jbrout import pyexiv
import pyexiv2


def rgb(r, g, b, a=00):
    return r * 256 * 256 * 256 + \
        g * 256 * 256 + \
        b * 256 + \
        a


class Img(object):
    def __init__(self, file=None, thumb=None, im=None):
        if file:
            try:
                im = GdkPixbuf.Pixbuf.new_from_file(file)
            except IOError:
                raise IOError()  # "Img() : file not found"
        elif thumb:
            extension = thumb.split('.')[-1].lower()
            try:
                # ~ fid = open(thumb, 'rb')
                # ~ jo = exif.process_file(fid)
                # ~ fid.close()
                # ~ data = jo["JPEGThumbnail"]

                img = pyexiv.Exiv2Metadata(pyexiv2.ImageMetadata(thumb))
                img.readMetadata()
                # XXX external call while pyexiv can't handle it
                if extension == 'nef':
                    data = Popen(["exiftool", "-b", "-PreviewImage",
                                  "%s" % thumb], stdout=PIPE).communicate()[0]
                else:
                    thumbnailData = img.getThumbnailData()
                    if len(thumbnailData) > 0:
                        data = thumbnailData[1]
                    else:
                        raise KeyError

                loader = gtk.gdk.PixbufLoader('jpeg')

                loader.write(data, len(data))
                im = loader.get_pixbuf()
                loader.close()
            except IOError:
                raise IOError()  # "Img() : file not found"
            except KeyError:
                raise KeyError()  # "Img() : no exif inside"
        elif im:
            pass
        else:
            raise Exception()  # "Img() : bad call"

        self.__im = im

    def __getWidth(self):
        return self.__im.get_width()
    width = property(__getWidth)

    def __getHeight(self):
        return self.__im.get_height()
    height = property(__getHeight)

    def __getPixbuf(self):
        return self.__im
    pixbuf = property(__getPixbuf)

    # ~ def getStreamJpeg(self, quality=70):
        # ~ f = StringIO()
        # ~ self.__im.save(f, "jpeg", quality=quality)
        # ~ f.seek(0)
        # ~ return f

    def resize(self, size):
        pb = self.__im
        (wx, wy) = self.width, self.height
        rx = 1.0 * wx / size
        ry = 1.0 * wy / size
        if rx > ry:
            rr = rx
        else:
            rr = ry

        # 3= best quality (gtk.gdk.INTERP_HYPER)
        pb = pb.scale_simple(int(wx / rr), int(wy / rr), 3)
        return Img(im=pb)

    def resizeC(self, size, color=rgb(0, 0, 0)):
        # ~ pb = gtk.gdk.Pixbuf(gtk.gdk.COLORSPACE_RGB, 0, 8, size, size)
        # ~ pb.fill(color)
        if color is not None:
            pb = gtk.gdk.Pixbuf(gtk.gdk.COLORSPACE_RGB, 0, 8, size, size)
            pb.fill(color)
        else:
            pb = gtk.gdk.Pixbuf(gtk.gdk.COLORSPACE_RGB, True, 8, size, size)
            pb.fill(0x00000000)

        newimg = self.resize(size)

        if newimg.width == size:
            x = 0
            y = (size - newimg.height) / 2
        else:
            x = (size - newimg.width) / 2
            y = 0
        newimg.__im.copy_area(0, 0, newimg.width, newimg.height, pb, x, y)
        return Img(im=pb)

    def save(self, dest, quality=80, format="jpeg"):
        assert type(dest) == unicode
        self.__im.save(dest, format, {"quality": str(quality)})


# Class pictureselector
# This class provides a thumbnailview with a slider. It behaves as a normaol
# gtk class, and emits the signal "value_changed" whenever a user changes the
# slider

class PictureSelector(Gtk.VBox):

    def __init__(self, photo_list):
        gtk.VBox.__init__(self)

        self.photo_list = photo_list

        # The integer cast is for the result is needed because the dates are
        # usually of type long, and a comparison needs an int
        # self.photo_list.sort(lambda f, s: int(int(s.date) - int(f.date)))

        self.photo_list.sort(lambda f, s: cmp(s.date, f.date))

        # Create all the visual elements
        self.thumb_display = gtk.Image()
        self.slider = gtk.HScrollbar()
        self.text_display = gtk.Label("Photo 1/1")
        self.pack_start(self.thumb_display, expand=False)
        self.pack_start(self.slider, expand=True, fill=True)
        self.pack_start(self.text_display, expand=False)

        # Initialize the slider
        if (len(self.photo_list) > 1):
            self.slider.set_range(1, len(self.photo_list))
            self.slider.set_increments(1, 10)

        self.updateDisplay()
        # --Instead of this, wouldnt it make sense just to not show the slider?
        # Otherwise the photo looks ugly all grey. See below
        # --Daniel Patterson (dbpatterson@riseup.net) 12th June 2007

        # Create the callbacks
        self.slider.connect("value_changed", self.onSliderChange)

        # Display everything
        if (len(self.photo_list) > 1):
            self.slider.show()
        self.text_display.show()
        self.thumb_display.show()

    def onSliderChange(self, widget):
        # Update the display of the text widget and the thumbnail
        self.updateDisplay()

        # Emit a signal that we have changed
        self.emit("value_changed", self)

    def getValue(self):
        # Returns the index value of the photolist. Watch out for off-by-one
        # errors!
        slider_value = int(self.slider.get_value())
        if (slider_value == 0):
            slider_value = 1
        return slider_value - 1

    def updateDisplay(self):
        photo_num = self.getValue()
        if photo_num < len(self.photo_list):
            self.text_display.set_text(
                "Photo %d/%d: %s" % (photo_num + 1, len(self.photo_list),
                                     self.photo_list[photo_num].name))
            self.thumb_display.set_from_pixbuf(
                self.photo_list[photo_num].getThumb())

    def set_sensitive(self, value):
        # Make the widget greyed out or active. If the photo list has only one
        # picture, it can never be active
        if value and (len(self.photo_list) < 2):
            value = False

        if value:
            gtk.VBox.set_sensitive(self, True)
        else:
            gtk.VBox.set_sensitive(self, False)

# Create the "value_changed" signal and connect it to the PictureSelector class
GObject.signal_new("value_changed", PictureSelector,
                   GObject.SIGNAL_RUN_LAST, GObject.TYPE_NONE,
                   (GObject.TYPE_PYOBJECT,))


class Buffer(object):
    size = None

    images = {}
    # ~ pixbufRefresh = gtk.gdk.pixbuf_new_from_file( "data/gfx/refresh.png" )
    pixbufRefresh = Img("data/gfx/refresh.png").pixbuf

    pbFolder = Img("data/gfx/folder.png").pixbuf
    pbBasket = Img("data/gfx/basket.png").pixbuf

    pbReadOnly = Img("data/gfx/check_no.png").pixbuf

    pbCheckEmpty = Img("data/gfx/check_false.png").pixbuf
    pbCheckInclude = Img("data/gfx/check_true.png").pixbuf
    pbCheckExclude = Img("data/gfx/check_no.png").pixbuf
    pbCheckDisabled = Img("data/gfx/check_disabled.png").pixbuf

    pixRaw = Img("data/gfx/raw.png").pixbuf

    # ~ @staticmethod
    # ~ def __thread(file, callback, callbackRefresh, item):
        # ~ do_gui_operation(Buffer.__fetcher, file, callback,
        #                   callbackRefresh, item)

    # ~ @staticmethod
    # ~ def __fetcher(file, callback, callbackRefresh, item):
        # ~ Buffer.images[file] = callback()
        # ~ if callbackRefresh and item>=0:
            # ~ callbackRefresh(item)

    # ~ @staticmethod
    # ~ def get(file, callback, callbackRefresh=None, item=None):
        # ~ """
        # ~ send a signal "refreshItem"(item) to object
        # ~ """
        # ~ if file in Buffer.images:
            # ~ return Buffer.images[file]
        # ~ else:
            # ~ thread.start_new_thread(Buffer.__thread,
            # ~ (file, callback, callbackRefresh, item) )
            # ~ return Buffer.pixbufRefresh

    @staticmethod
    def remove(file):
        if file in Buffer.images:
            del(Buffer.images[file])
            return True
        else:
            return False

    @staticmethod
    def clear():
        size = Buffer.size or 160
        Buffer.images = {}
        Buffer.pixbufNF = Img("data/gfx/imgNotFound.png").resizeC(size).pixbuf
        Buffer.pixbufNFNE = Img("data/gfx/imgNotFound.png").resizeC(
            size, rgb(255, 0, 0)).pixbuf

        Buffer.pixbufNT = Img("data/gfx/imgNoThumb.png").resizeC(size).pixbuf
        Buffer.pixbufNTNE = Img("data/gfx/imgNoThumb.png").resizeC(
            size, rgb(255, 0, 0)).pixbuf

        Buffer.pixbufERR = Img("data/gfx/imgError.png").resizeC(size).pixbuf
        Buffer.pixbufERRNE = Img("data/gfx/imgError.png").resizeC(
            size, rgb(255, 0, 0)).pixbuf

if __name__ == "__main__":
    l = [('ana', 'potes'), ('Anna', 'voisin'), ('beer', 'drinks')]
    w = WinKeyTag("apply this tag", "", l)
    w.loop()
