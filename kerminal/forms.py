# encoding: utf-8

"""

"""

from functools import partial
from time import strftime, sleep

from npyscreen import ButtonPress, Form
import npyscreen
import logging

log = logging.getLogger('kerminal.forms')

from . import __version__
from .widget_bases import LiveTitleText


#The FormWithLiveWidgets class represents one of the first strategies for
#improving the means by which live widgets are integrated with forms. I highly
#suspect that other strategies may be explored, especially as I consider the
#topic of widget clusters. I'll need to delve into the source code for Widgets
#and the `add` method, it might be that I should just add an attribute to a
#base implementation for a LiveWidget and let `add` assign the function
class FormWithLiveWidgets(Form):
    """
    The `FormWithLiveWidgets` modifies the basic `Form` in a small way to
    enhance the convenience of working with "live" widgets.

    For live-updating data, the form's `while_waiting` method will be employed
    to instruct all live widgets to update their values and then the screen will
    be updated. Live widgets need to have a special method, known as `feed`,
    which is called to update the widget's value, and the live widgets must be
    registered with the Form so that each widget's `feed` method can be called
    appropriately.

    """
    live_widgets = []

    def add_live(self, *args, **kwargs):
        live_widget = self.add(*args, **kwargs)
        self.live_widgets.append(live_widget)
        return live_widget

    def while_waiting(self):
        #Updates all live widgets from their feed before updating
        for live_widget in self.live_widgets:
            live_widget.feed()
        self.display()


class Connection(FormWithLiveWidgets):
    OK_BUTTON_TEXT = 'DROP CONNECTION'

    def create(self):
        #self.parentApp.stream.start()
        self.add(npyscreen.FixedText, value='You have successfully connected!')
        self.time_w = self.add_live(LiveTitleText,
                                    name='Time',
                                    value='',
                                    editable=False,
                                    #feed=lambda:self.parentApp.data.get('v.altitude'))
                                    feed=partial(strftime, "%Y-%m-%d %H:%M:%S")
                                    )
        self.alt = self.add_live(LiveTitleText,
                                 name='V. Altitude',
                                 value='',
                                 editable=False,
                                 feed=partial(self.parentApp.stream.data.get, 'v.altitude')
                                 )
        self.mission_time = self.add_live(LiveTitleText,
                                          name='V. Mission Time',
                                          value='',
                                          editable=False,
                                          feed=partial(self.parentApp.stream.data.get, 'v.missionTime')
                                          )
        self.univ_time = self.add_live(LiveTitleText,
                                       name='Universal Time',
                                       value='',
                                       editable=False,
                                       feed=partial(self.parentApp.stream.data.get, 't.universalTime')
                                       )
        self.paused = self.add_live(LiveTitleText,
                                    name='Game Paused',
                                    value='',
                                    editable=False,
                                    feed=lambda: str(bool(partial(self.parentApp.stream.data.get, 'p.paused')))
                                    )

    def afterEditing(self):
        self.parentApp.stream.loop.stop()
        self.parentApp.stream.make_connection.clear()
        #self.parentApp.stream.connect_event.clear()
        self.parentApp.setNextForm('MAIN')


class ConnectionButton(ButtonPress):

    def whenPressed(self):
        #Sanity checking of fields
        address = self.parent.address.value
        port = self.parent.port.value
        if not address or not port:
            self.parent.info.value = 'You must enter an address AND a port!'
            self.parent.display()
            return
        try:
            port = int(port)
        except ValueError:
            self.parent.info.value = 'The port must be a number!'
            self.parent.display()
            return

        #Instructions to the Communication Thread to make the connection
        self.parent.parentApp.stream.address = address
        self.parent.parentApp.stream.port = port
        self.parent.parentApp.stream.make_connection.set()

        self.parent.info.value = 'Making connection...'
        self.parent.display()

        #Wait for the Communication Thread to tell us it is done
        self.parent.parentApp.stream.connect_event.wait()
        self.parent.parentApp.stream.connect_event.clear()

        if self.parent.parentApp.stream.connected:  # Success
            self.parent.parentApp.switchForm('CONNECTION')
            self.parent.special_button = True  # See ConnectQuery.afterEditing

        else:  # Failed
            self.parent.info.value = 'Could not connect'
            self.parent.display()


class ConnectQuery(Form):
    OK_BUTTON_TEXT = 'EXIT'
    special_button = False
    FIX_MINIMUM_SIZE_WHEN_CREATED = True

    def create(self):
        self.add(npyscreen.FixedText,
                 value='Welcome to Kerminal {0}'.format(__version__),
                 editable=False)
        self.address = self.add(npyscreen.TitleText,
                                name='Address:',
                                value='')
        self.port = self.add(npyscreen.TitleText,
                             name='Port:',
                             value='8085')
        self.connect = self.add(ConnectionButton, name='Connect')
        self.info = self.add(npyscreen.FixedText,
                             value='',
                             editable=False)

    def beforeEditing(self):
        pass

    def afterEditing(self):
        #Contrary to the documentation, switchForm will not evade the exit
        #logic of the Form, so this check is needed
        if not self.special_button:
            self.parentApp.setNextForm(None)
        self.special_button = False
        self.info.value = ''
