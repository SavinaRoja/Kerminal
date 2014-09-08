# encoding: utf-8

"""

"""

from npyscreen import ButtonPress, Form
import npyscreen

from . import __version__


class ConnectionButton(ButtonPress):

    def whenPressed(self):
        #self.parent.parentApp.switchForm('CONNECTION')
        self.parent.special_button = True

class ConnectQuery(Form):
    OK_BUTTON_TEXT = 'EXIT'
    special_button = False

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
