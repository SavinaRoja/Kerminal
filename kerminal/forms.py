# encoding: utf-8

"""

"""

from functools import partial
from time import strftime

from npyscreen import ButtonPress, Form
import npyscreen
import logging

log = logging.getLogger('kerminal.forms')

from . import __version__


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
        """
        A special wrapper around `Form.add` that intercepts the
        keyword argument "feed" in order to register the
        """
        if 'feed' not in kwargs:
            feed = lambda: 'NULL'
        else:
            feed = kwargs.pop('feed')
        live_widget = self.add(*args, **kwargs)
        live_widget.feed = feed
        self.live_widgets.append(live_widget)
        return live_widget

    def while_waiting(self):
        #Updates all live widgets from their feed before updating
        for live_widget in self.live_widgets:
            live_widget.value = live_widget.feed()
        self.display()


class Connection(FormWithLiveWidgets):
    OK_BUTTON_TEXT = 'DROP CONNECTION'

    def create(self):
        #self.parentApp.stream.start()
        self.add(npyscreen.FixedText, value='You have successfully connected!')
        self.time_w = self.add_live(npyscreen.TitleText,
                                    name='Time',
                                    value='',
                                    editable=False,
                                    #feed=lambda:self.parentApp.data.get('v.altitude'))
                                    feed=partial(strftime, "%Y-%m-%d %H:%M:%S"))

    def afterEditing(self):
        self.parentApp.setNextForm('MAIN')


class ConnectionButton(ButtonPress):

    def whenPressed(self):
        self.parent.parentApp.switchForm('CONNECTION')
        self.parent.special_button = True


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
        self.checkbox = self.add(npyscreen.CheckBox,
                                 name='Add this to defaults?')
        self.connect = self.add(ConnectionButton, name='Connect')

    def beforeEditing(self):
        pass

    def afterEditing(self):
        #Contrary to the documentation, switchForm will not evade the exit
        #logic of the Form, so this check is needed
        if not self.special_button:
            self.parentApp.setNextForm(None)
        self.special_button = False
