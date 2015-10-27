# -*- coding: utf-8 -*-

"""
changelog:
 - right button doesn't deselect anymore, on a selection
 - click on a already selected item in a selection, make this the only selected
 - better display text under thumbnails
"""
import sys

from gi.repository import Gtk, GObject, Pango, GdkPixbuf, Gdk

from g.gui.common.rectangle import Rectangle
from g.gui.common.layoutengine import LayoutEngine

import time
import os

BORDER_SIZE = 2
CELL_BORDER_WIDTH = 4
SELECTION_THICKNESS = 2

GObject.threads_init()

class Rect(object):
    def __init__(self, x, y, w, h):
        self.x = x
        self.y = y
        self.w = w
        self.h = h

def rectIntersect(a, b):
    x1, y1, w1, h1 = a[0], a[1], a[2], a[3]
    x2, y2, w2, h2 = b[0], b[1], b[2], b[3]

    r1left = x1
    r2left = x2
    r1right = x1 + w1
    r2right = x2 + w2
    r1bottom = y1 + h1
    r2bottom = y2 + h2
    r1top = y1
    r2top = y2

    left = max(r1left, r2left)
    right = min(r1right, r2right)
    bottom = min(r1bottom, r2bottom)
    top = max(r1top, r2top)

    width = right - left
    height = bottom - top

    if (width <= 0) or (height <= 0):
        return None
    else:
        return (left, top, width, height)

class Selection:
    def __init__(self):
        self.real_selection = []
        self.frozen = False
        self.notify_callbacks = []

    def __iter__(self):
        return iter(self.real_selection)

    def __len__(self):
        return len(self.real_selection)

    def __getitem__(self, key):
        return self.real_selection[key]

    def __setitem__(self, key, value):
        old_selection = self.real_selection[:]
        self.real_selection[key] = value
        self.notify_changes(old_selection)

    def __delitem__(self, key):
        old_selection = self.real_selection[:]
        del self.real_selection[key]
        self.notify_changes(old_selection)

    def append(self, val):
        old_selection = self.real_selection[:]
        self.real_selection.append(val)
        self.notify_changes(old_selection)

    def remove(self, val):
        old_selection = self.real_selection[:]
        self.real_selection.remove(val)
        self.notify_changes(old_selection)

    def empty(self):
        old_selection = self.real_selection[:]
        self.real_selection = []
        self.notify_changes(old_selection)

    def set(self, val):
        old_selection = self.real_selection[:]
        self.real_selection = val
        self.notify_changes(old_selection)

    def freeze(self):
        self.frozen = True
        self.old_selection = self.real_selection[:]

    def thaw(self):
        self.frozen = False
        self.notify_changes(self.old_selection)

    def notify_changes(self, old_selection):
        if self.frozen:
            return
        if old_selection == self.real_selection:
            return
        for callback in self.notify_callbacks:
            callback(old_selection)

    def add_notify_callback(self, callback):
        self.notify_callbacks.append(callback)

selection = Selection()



class ThumbnailsView(Gtk.Layout):
    scroll_value = 0
    scroll = False

    real_focus_cell = 0

    # initial thumbnail size
    real_thumbnail_width = 160
    thumbnail_height = 160

    sort_by = 'date'
    reversed_sort_order = False

    priority_loads = []

    def __init__(self):
        Gtk.Layout.__init__(self)

        self.thumbCache = {}
        self.layoutEngine = LayoutEngine()
        self.loading_pixbuf = GdkPixbuf.Pixbuf.new_from_file('data/gfx/refresh.png')
        self.selection = selection
        self.thumbnail_pixbufs = {}
        self.exif_tags = {}

        self.height = 100
        self.width = 100
        self.visible = Rectangle(0, 0, 1, 1)

        self.connect('draw', self.on_draw_event)
        self.connect('key-press-event', self.on_key_press)
        self.set_can_focus(True)

        self.items = []
        self.update_layout()
        selection.add_notify_callback(self.notify_selection_change)
        self.hdl = None

        vadj = self.get_vadjustment()
        hadj = self.get_hadjustment()

        vadj.connect('value-changed', self.on_adjustment_value_changed)
        hadj.connect('value-changed', self.on_adjustment_value_changed)
        Gtk.Scrollable.set_vadjustment(self, vadj)
        Gtk.Scrollable.set_hadjustment(self, hadj)

    def __load_thumbnails_bg(self):
        while True:
            if self.priority_loads:
                idx = self.priority_loads.pop(0)
                self.get_thumb(idx)
                self.invalidate_cell(idx)
            time.sleep(0.01)
            yield True

    def get_thumb(self, idx):
        """ create a PixBuf containing the image's thumb and flags images
        (basket, read-only, raw) the image's full path is used as buffer's key
        """
        node = self.items[idx]
        if not self.is_thumb(idx):
            Buffer.images[node.file] = node.getThumb()
        pb = Buffer.images[node.file]
        pb2 = 0

        if node.isInBasket:
            if pb2 == 0:
                pb2 = pb.copy()
            Buffer.pbBasket.copy_area(0, 0, 15, 13, pb2, 7, 7)

        if node.isReadOnly:
            if pb2 == 0:
                pb2 = pb.copy()
            wx = pb.get_width()
            Buffer.pbReadOnly.copy_area(0, 0, 15, 13, pb2, wx - 22, 7)

        if node.rating:
            if pb2 == 0:
                pb2 = pb.copy()
            i = 0
            while i < node.rating:
                Buffer.pbReadOnly.copy_area(5, 4, 5, 5, pb2, 25 + 7 * i, 11)
                i += 1

        if pb2 != 0:
            pb = pb2

        return pb


    def stop(self):
        """ stop background process which load thumbs """
        if self.hdl:
            GObject.source_remove(self.hdl)
            self.hdl = None

    def start(self):
        """ start background process to load thumbs """
        if not self.hdl:
            gen = self.__load_thumbnails_bg()
            def f():
                return next(gen)
            self.hdl = GObject.idle_add(f)

    def set_photos(self, photos):
        self.stop()

        self.items = photos
        # ~ self.sort_photos(photos)
        self.update_layout()
        self.selection.empty()

        self.priority_loads = []

        self.start()

    def get_thumbnail_width(self):
        return self.real_thumbnail_width

    def set_thumbnail_width(self, value):
        self.thumbnail_height = value  # int(value * 3./4)
        self.real_thumbnail_width = int(value)
        self.invalidate_view()
        self.update_layout()
    thumbnail_width = property(get_thumbnail_width, set_thumbnail_width)

    def on_key_press(self, widget, event):
        shift = event.state & (Gdk.KEY_Shift_L | Gdk.KEY_Shift_R)
        ctrl = event.state & (Gdk.KEY_Control_L | Gdk.KEY_Control_R)
        focus_old = self.focus_cell
        if event.keyval == Gdk.KEY_Down:
            self.focus_cell += self.cells_per_row
        elif event.keyval == Gdk.KEY_Left:
            if ctrl and shift:
                self.focus_cell -= self.focus_cell % self.cells_per_row
            else:
                self.focus_cell -= 1
        elif event.keyval == Gdk.KEY_Right:
            if ctrl and shift:
                self.focus_cell += self.cells_per_row - \
                    (self.focus_cell % self.cells_per_row) - 1
            else:
                self.focus_cell += 1
        elif event.keyval == Gdk.KEY_Up:
            self.focus_cell -= self.cells_per_row
        elif event.keyval == Gdk.KEY_Home:
            self.focus_cell = 0
        elif event.keyval == Gdk.KEY_End:
            self.focus_cell = len(self.items) - 1
        elif ctrl and event.keyval == ord('a'):  # select All
            self.selection.set(range(0, len(self.items)))
        else:
            return False

        self.focus_cell = max(self.focus_cell, 0)
        self.focus_cell = min(self.focus_cell, len(self.items) - 1)

        if self.focus_cell == focus_old:
            # so up from the first or down from the last doesn't tab
            # to the prev/next widget
            return True

        self.selection.freeze()

        if shift:
            if focus_old != self.focus_cell and focus_old in self.selection \
                    and self.focus_cell in self.selection:
                for i in range(min(focus_old, self.focus_cell) + 1,
                               max(focus_old, self.focus_cell) + 1):
                    if i in self.selection:
                        self.selection.remove(i)
            else:
                for i in range(min(focus_old, self.focus_cell),
                               max(focus_old, self.focus_cell) + 1):
                    if not i in self.selection:
                        self.selection.append(i)

        else:
            self.selection.set([self.focus_cell])

        self.selection.thaw()

        self.scroll_to(self.focus_cell)
        return True

    def on_adjustment_value_changed(self, adj, *args):
        self.visible.y = int(adj.get_value())
        self.do_scroll()

    def onHAdjustmentValueChanged(self, adj, *args):
        self.do_scroll()

    def do_scroll(self):
        pass

    def update_layout(self, rectangle=None):
        if rectangle is None:
            rectangle = self.get_allocation()

        self.layoutEngine.updateWidth(rectangle.width)
        self.layoutEngine.updateCells(len(self.items), self.thumbnail_width, self.thumbnail_height)
        self.height = self.layoutEngine.getHeight()

        self.visible.width = rectangle.width
        self.visible.height = rectangle.height


        vadjustment = self.get_vadjustment()
        hadjustment = self.get_hadjustment()
        vadjustment.step_increment = self.thumbnail_height
        vadjustment.connect('value-changed', self.on_adjustment_value_changed)
        x = hadjustment.get_value()
        y = self.height * self.scroll_value
        self.set_size(x, y, self.visible.width, self.height)

    def set_size(self, x, y, width, height):
        vadjustment = self.get_vadjustment()
        hadjustment = self.get_hadjustment()

        xchange = False
        ychange = False

        hadjustment.upper = max(self.get_allocation().width, width)
        vadjustment.upper = max(self.get_allocation().height, height)

        if self.scroll:
            xchange = (hadjustment.value != x)
            ychange = (vadjustment.value != y)
            self.scroll = False

        if self.get_realized():
            self.get_bin_window().freeze_updates()
            #self.bin_window.freeze_updates()

        if xchange or ychange:
            if self.get_realized():
                self.bin_window.move_resize(-x, -y, hadjustment.upper,
                                            vadjustment.upper)
                vadjustment.value = y
                hadjustment.value = x

        if self.scroll:
            self.scroll = False

        if width != self.get_allocation().width or height != self.get_allocation().height:
            Gtk.Layout.set_size(self, width, height)

        if xchange or ychange:
            vadjustment.change_value()
            hadjustment.change_value()

        if self.get_realized():
            self.get_bin_window().thaw_updates()
            self.get_bin_window().process_updates(True)

    def on_draw_event(self, widget, context):
        alloc = self.get_allocation()
        area = [alloc.x, alloc.y, self.get_allocated_width(), self.get_allocated_height()]

        # context.set_source_rgb(0, 0, 0)
        # context.set_line_width(0.5)
        # context.rectangle(10, 10, 10, 20)
        #
        # import random
        # mx = min(alloc.width, alloc.height)
        # self.coords = []
        # for _ in range(30):
        #     self.coords.append((random.randint(0, mx), random.randint(0, mx)))
        # for i in self.coords:
        #     for j in self.coords:
        #         context.move_to(i[0], i[1])
        #         context.line_to(j[0], j[1])
        #         context.stroke()

        print(self.visible)
        self.draw_all_cells(self.visible, context)
        context.stroke()
        return False

    def get_cell_position(self, cell_num):
        if self.cells_per_row == 0:
            return 0, 0

        row, col = divmod(cell_num, self.cells_per_row)

        x = col * self.cell_width + BORDER_SIZE
        y = row * self.cell_height + BORDER_SIZE

        return x, y

    def draw_all_cells(self, area, cr):
        cells = self.layoutEngine.getVisibleCells(area)
        for cellNum, cell in cells.items():
            self.drawCell(cr, cell, cellNum)

    def drawCell(self, cr, cell, cellNum):
        img = self.items[cellNum]
        fname = img.file
        thumb = self.thumbCache.get(fname)
        print('draw thumb: ', fname )
        if not thumb:
            thumb = GdkPixbuf.Pixbuf.new_from_file(fname)
            thumb = thumb.scale_simple(self.thumbnail_width, self.thumbnail_height,
                    GdkPixbuf.InterpType.BILINEAR)
            self.thumbCache[fname] = thumb
        x = cell.x - self.visible.x
        y = cell.y - self.visible.y
        Gdk.cairo_set_source_pixbuf(cr, thumb, x, y)
        cr.paint()
        cr.stroke()

        # cr.rectangle(cell.x - self.visible.x, cell.y - self.visible.y, cell.width, cell.height)
        # self.get_thumbnail_pixbuf(cellNum)
        # cr.stroke()

    def cell_bounds(self, cell, cr):
        x, y = self.get_cell_position(cell)
        return [x, y, self.cell_width, self.cell_height]


    def get_thumbnail_pixbuf(self, thumbnail_num):
        if not self.is_thumb(thumbnail_num):
            if thumbnail_num in self.priority_loads:
                self.priority_loads.remove(thumbnail_num)
            self.priority_loads.insert(0, thumbnail_num)
            pixbuf = self.loading_pixbuf
        else:
            pixbuf = self.get_thumb(thumbnail_num)
            if pixbuf.get_width() > pixbuf.get_height():
                wx, wy = self.thumbnail_width, self.thumbnail_height
            else:
                r = float(pixbuf.get_height()) / self.thumbnail_height
                wx, wy = int(pixbuf.get_width() / r), self.thumbnail_height
            # ~ pixbuf = pixbuf.scale_simple(wx, wy, gtk.gdk.INTERP_BILINEAR)
            pixbuf = pixbuf.scale_simple(wx, wy, gtk.gdk.INTERP_NEAREST)
        return pixbuf

    def draw_cell(self, thumbnail_num, area, cr):
        bounds = self.cell_bounds(thumbnail_num, cr)

        ins = rectIntersect(bounds, area)
        if not rectIntersect(bounds, area):
            return

        # a = GdkPixbuf.Pixbuf.new_from_file('/media/data/ph/marn2/DSC_0647.JPG')
        # a = a.scale_simple(150, 150, GdkPixbuf.InterpType.BILINEAR)
        # thumbnail = a.scale_simple(self.cell_width, self.cell_height, GdkPixbuf.InterpType.BILINEAR)
        # Gdk.cairo_set_source_pixbuf(cr, a, a.get_width(), a.get_height())
        # cr.paint()
        # cr.stroke()

        thumbnail = self.get_thumbnail_pixbuf(thumbnail_num)
        selected = thumbnail_num in self.selection
        if selected:
            if self.has_focus():
                cell_state = Gtk.StateFlags.SELECTED
            else:
                cell_state = Gtk.StateFlags.ACTIVE
        else:
            cell_state = Gtk.StateFlags.NORMAL
        if thumbnail != self.loading_pixbuf:
            cr.rectangle(bounds[0], bounds[1], bounds[2] - 1, bounds[3] - 1)
            # self.style.paint_flat_box(self.bin_window, cell_state,
            #                           gtk.SHADOW_OUT, area, self,
            #                           'ThumbnailsView',
            #                           bounds.x, bounds.y,
            #                           bounds.width - 1, bounds.height - 1)

        def inflate(rect, x, y):
            return (rect[0] - x, rect[1] - y, rect[2] + 2*x, rect[3]+2*y)

        #isFocused = False

        if self.has_focus() and thumbnail_num == self.focus_cell:
            focus = inflate(bounds, -3, -3)

            # self.get_style().paint_focus(self.bin_window, cell_state,
            #                        area, self, None, focus.x, focus.y,
            #                        focus.width, focus.height)
            #isFocused = True

        region = (0, 0, 0, 0)
        image_bounds = inflate(bounds, -CELL_BORDER_WIDTH, -CELL_BORDER_WIDTH)

        if selected:
            expansion = SELECTION_THICKNESS
        else:
            expansion = 0

        boundsInflated = inflate(image_bounds, expansion + 1, expansion + 1)
        image_bounds = rectIntersect(image_bounds, area)
        if image_bounds[2]:
            def fit(orig_width, orig_height, dest_width, dest_height):
                if orig_width == 0 or orig_height == 0:
                    return 0, 0
                scale = min(dest_width / orig_width, dest_height / orig_height)
                if scale > 1:
                    scale = 1
                fit_width = scale * orig_width
                fit_height = scale * orig_height
                return fit_width, fit_height

            # resizing during the painting (pn.getThumb give some 160x160)
            w, h = fit(thumbnail.get_width(), thumbnail.get_height(),
                       self.thumbnail_width, self.thumbnail_width)

            # resizing during the extraction (pn.getThumb desired size)
            # w, h = fit(thumbnail.get_width(), thumbnail.get_height(),
            #            160, 160)

            cr.set_line_width(1)
            cr.set_source_rgb(0, 0, 0)
            cr.rectangle(10, 10, 10, 10)
            region = cr.rectangle(bounds[0], bounds[1], bounds[2], bounds[3])
            region = bounds
            #     bounds.x + (bounds.width - w) / 2,
            #     bounds.y + self.thumbnail_height - h + CELL_BORDER_WIDTH,
            #     w, h)

            # EXPAND WHEN SELECTED !
            region = inflate(region, expansion, expansion)
            region = (region[0], region[1], max(1, region[2]), max(1, region[3]))

            #a = GdkPixbuf.Pixbuf.new_from_file('/media/data/ph/marn2/DSC_0647.JPG')

            if region[2] != thumbnail.get_width() and region[3] != thumbnail.get_height():
                # the speedest
                temp_thumbnail = thumbnail.scale_simple(region[2], region[3],
                        GdkPixbuf.InterpType.BILINEAR)
            else:
                temp_thumbnail = thumbnail

            region = (region[0], region[1], temp_thumbnail.get_width(), temp_thumbnail.get_height())

            draw = inflate(region, 1, 1)

            # if thumbnail != self.loading_pixbuf:
            #     self.style.paint_shadow(self.bin_window, cell_state,
            #                             gtk.SHADOW_OUT, area, self,
            #                             'ThumbnailsView', draw.x,
            #                             draw.y, draw.width, draw.height)

            draw = rectIntersect(region, area)
            if draw[2]:
                cr.rectangle(draw[0], draw[1], draw[2], draw[3])

                # Gdk.cairo_set_source_pixbuf(cr, a, draw[0], draw[1])
                # cr.paint()
                # cr.stroke()

                # self.get_bin_window().draw_pixbuf(
                #     self.style.white_gc,
                #     temp_thumbnail,
                #     draw.x - region.x,
                #     draw.y - region.y,
                #     draw.x, draw.y,
                #     draw.width, draw.height,
                #     gtk.gdk.RGB_DITHER_NONE,
                #     draw.x, draw.y)

        layout_bounds = (0, 0, 0, 0)

        item = self.items[thumbnail_num]
        if item:
            layout = Pango.Layout(self.get_pango_context())
            layout.set_font_description(self.get_style().font_desc)
            t = self.get_text(thumbnail_num)
            layout.set_text(t, len(t))

            # ~ if isFocused:
            layout.set_width((region[2] + 6) * 1000)
            layout.set_wrap(1)

            layout_bounds = (layout_bounds[0], layout_bounds[1]) + layout.get_pixel_size()
            lbX = bounds[0] + (bounds[2] - layout_bounds[2]) / 2
            lbY = bounds[1] + bounds[3] - CELL_BORDER_WIDTH - layout_bounds[3] + 3
            layout_bounds = (lbX, lbY) + layout_bounds[2:]
            region = rectIntersect(layout_bounds, area)
            if region is None:
                region = (0, 0, 0, 0)
            if region[2]:
                cr.rectangle(layout_bounds[0], layout_bounds[1], layout_bounds[2],
                             layout_bounds[3])
                # self.style.paint_flat_box(self.bin_window, cell_state,
                #                           gtk.SHADOW_OUT, area, self,
                #                           'ThumbnailsView',
                #                           layout_bounds.x,
                #                           layout_bounds.y,
                #                           layout_bounds.width,
                #                           layout_bounds.height)
                #
                # self.style.paint_layout(self.bin_window, cell_state,
                #                         True, area, self,
                #                         'ThumbnailsView',
                #                         layout_bounds.x,
                #                         layout_bounds.y, layout)

    def scroll_to(self, cell_num, center=True):
        if not self.get_realized():
            return
        adjustment = self.get_vadjustment()
        x, y = self.get_cell_position(cell_num)
        if y + self.cell_height > adjustment.upper:
            self.update_layout()

        if center:
            t = y + self.cell_height / 2 - adjustment.page_size / 2
            if t < 0:
                t = 0
            elif t + adjustment.page_size > adjustment.upper:
                t = adjustment.upper - adjustment.page_size
            adjustment.value = t
        else:
            adjustment.value = y


class ListView(ThumbnailsView):
    allow_drag = True
    allow_drop = True

    def __init__(self):
        ThumbnailsView.__init__(self)
        self.set_visible(True)

    def on_drag_data_received_data(self, widget, object, x, y, sdata, code,
                                   time):
        """ event drop notified """
        cell_num = self.cell_at_position(x, y, False)
        if cell_num >= 0:
            if cell_num not in self.selection:
                self.selection.set([cell_num])

    def notify_selection_change(self, old):
        """ event selection changed """
        ThumbnailsView.notify_selection_change(self, old)

    def getSelected(self):
        return [self.items[i] for i in self.selection.real_selection]

    def init(self, l):
        self.set_photos(l)

    def get_text(self, idx):
        item = self.items[idx]
        return item.display

    def get_thumb(self, idx):
        item = self.items[idx]
        return Cache.get(item)

    def is_thumb(self, idx):
        item = self.items[idx]
        return Cache.exists(item)

class Cache:
    __buf = {}

    @staticmethod
    def exists(item):
        return item.file in Cache.__buf

    @staticmethod
    def get(item):
        if not Cache.exists(item):
            Cache.__buf[item.file] = item.getThumb()
        return Cache.__buf[item.file]


class ImageFile(object):

    def __getAff(self):
        return os.path.basename(self.__file)
    display = property(__getAff)

    def __getFile(self):
        return self.__file
    file = property(__getFile)

    def __init__(self, file):
        """ constructor of a ImageFile """
        self.__file = file

    @staticmethod
    def load(path):
        """ constructor of a list of ImageFile """
        ll = []
        for filename in os.listdir(path):
            if not os.path.splitext(filename)[1].lower() in ('.jpg', '.jpeg'):
                continue
            ll.append(ImageFile(os.path.join(path, filename)))
        return ll

if __name__ == '__main__':
    THUMBNAILS_CACHE_SIZE = 10  # so it tests lazy-loading
    if len(sys.argv) == 2:
        path_base = sys.argv[1]
    else:
        path_base = '/media/data/ph/marn2/'

    p = TestLayoutMgr(path_base)
    p.run()
    p.destroy()
