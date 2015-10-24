from gi.repository import Gtk, GObject

class GToolButton(object):
    def __init__(self, buttonId : str, text : str, icon):
        self.id = buttonId
        self.text = text
        self.icon = icon


class GToolBar(Gtk.VBox):
    __gtype_name__ = 'GToolBar'

    def __init__(self, buttons):

        super().__init__()

        self.buttons = {}
        self.selectedId = None
        for button in buttons:
            props = GToolBar.createButton(button.text, button.icon)
            eventBox = props['eventBox']
            eventBox.connect('button-press-event', self.onButtonPress, button.id)
            self.buttons[button.id] = props
            self.pack_start(eventBox, False, False, 0)

        self.set_visible(True)

    def onButtonPress(self, widget, event, buttonId):
        if self.selectedId == buttonId and self.selectedId is not None:
            GToolBar.changeButtonState(self.buttons[buttonId], False)
            self.selectedId = None
            self.emit('selection-changed', None)
        else:
            for key, value in self.buttons.items():
                if key != buttonId:
                    GToolBar.changeButtonState(value, False)
                else:
                    self.selectedId = buttonId
                    GToolBar.changeButtonState(value, True)
            self.emit('selection-changed', buttonId)

    @staticmethod
    def changeButtonState(button : dict, state : bool):
        if state:
            button['frame'].set_shadow_type(Gtk.ShadowType.ETCHED_IN)
            button['label'].set_visible(True)
        else:
            button['frame'].set_shadow_type(Gtk.ShadowType.NONE)
            button['label'].set_visible(False)


    @staticmethod
    def createButton(text, buttonIcon):
        # create
        eventBox = Gtk.EventBox()
        frame = Gtk.Frame()
        layout = Gtk.VBox()
        label = Gtk.Label(text)
        icon = Gtk.Image()

        # properties
        eventBox.set_visible(True)
        frame.set_visible(True)
        layout.set_visible(True)
        label.set_visible(False)
        icon.set_visible(True)
        if type(buttonIcon) == str:
            icon.set_from_icon_name(buttonIcon, Gtk.IconSize.BUTTON)
        label.set_angle(90)

        # packing
        layout.pack_start(label, False, False, 0)
        layout.pack_start(icon, False, False, 0)
        frame.add(layout)
        eventBox.add(frame)

        return {'eventBox': eventBox, 'frame': frame, 'layout': layout,
                'label': label, 'icon': icon}


GObject.signal_new('selection-changed', GToolBar, GObject.SIGNAL_RUN_LAST,
        GObject.TYPE_PYOBJECT, (GObject.TYPE_PYOBJECT, ))