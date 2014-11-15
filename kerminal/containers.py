# encoding: utf-8

import npyscreen2
from .widgets import SemiInteractiveText

import curses
from functools import partial
import logging


class EscapeForwardingContainer(npyscreen2.Container):
    def set_up_exit_condition_handlers(self):
        super(EscapeForwardingContainer, self).set_up_exit_condition_handlers()
        self.how_exited_handlers.update({'escape': self.h_exit_escape})


class EscapeForwardingSmartContainer(EscapeForwardingContainer,
                                     npyscreen2.SmartContainer):
    pass


class EscapeForwardingGridContainer(EscapeForwardingContainer,
                                    npyscreen2.GridContainer):
    pass


#MultiLine widgets are likely to be built into npyscreen2 in the future, for now
#I am experimenting with them here
class KerminalMultiLineText(EscapeForwardingContainer, npyscreen2.Container):

    def resize(self):
        cur_y = self.rely + self.top_margin - self.show_from_y

        for i, widget in enumerate(self.autoables):
            widget.rely = cur_y + i
            widget.relx = self.relx + self.left_margin

    def build_contained_from_text(self, text, overwrite=True):
        if overwrite:
            self.contained = [w for w in self.contained if not w.auto_manage]
        for line in text.splitlines():
            self.add(SemiInteractiveText,
                     value=line.strip())

    def set_up_handlers(self):
        super(EscapeForwardingContainer, self).set_up_handlers()
        self.handlers.update({curses.KEY_NPAGE: self.h_scroll_page_down,
                              curses.KEY_PPAGE: self.h_scroll_page_up})

    def h_scroll_page_down(self, inpt=None):
        #Breaks the edit_loop of the current text field
        self.contained[self.edit_index].editing = False

        effective_page = self.height - (self.top_margin + self.bottom_margin)
        self.edit_index += effective_page

        #Avoid runoff
        if self.edit_index > len(self.contained):
            self.edit_index = len(self.contained) - 1

        #If the selected widget is not an autoable, move forward up to end
        if not self.contained[self.edit_index].auto_manage:
            for i, widget in enumerate(self.contained[self.edit_index + 1:]):
                if widget.auto_manage:
                    self.edit_index += i + 1
                    break

        #If the following is True, then the previous has failed and for whatever
        #reason, we were already passed the last autoable to begin with
        #So we'll just pick the last autoable
        if not self.contained[self.edit_index].auto_manage:
            self.edit_index = self.contained.index(self.autoables[-1])

    def h_scroll_page_up(self, inpt=None):
        self.contained[self.edit_index].editing = False

        effective_page = self.height - (self.top_margin + self.bottom_margin)
        self.edit_index -= effective_page

        #Avoid runoff
        if self.edit_index < 0:
            self.edit_index = 0

        #If the selected widget is not an autoable, move backwards up to begin
        if not self.contained[self.edit_index].auto_manage:
            for i, widget in enumerate(self.contained[:self.edit_index: -1]):
                if widget.auto_manage:
                    self.edit_index -= i + 1
                    break

        #If the following is True, then the previous has failed and for whatever
        #reason, we were already passed the first autoable to begin with
        #So we'll just pick the first autoable
        if not self.contained[self.edit_index].auto_manage:
            self.edit_index = self.contained.index(self.autoables[0])


class KerminalLivePlotable(EscapeForwardingContainer):

    def __init__(self,
                 form,
                 parent,
                 header='header',
                 title_length=10,
                 margin=1,
                 container_editable_as_widget=True,
                 *args,
                 **kwargs):
        self.title_length = title_length
        super(KerminalLivePlotable, self).__init__(form,
                                                   parent,
                                                   margin=margin,
                                                   container_editable_as_widget=container_editable_as_widget,
                                                   *args,
                                                   **kwargs)

        self.border = self.add(npyscreen2.BorderBox,
                               widget_id='border',
                               auto_manage=False,
                               editable=False)
        self.header = self.add(npyscreen2.TextField,
                               widget_id='header',
                               auto_manage=False,
                               editable=False,
                               value=header,
                               color='Label')

    def pre_edit(self):
        self.container_selected = True
        self.border.highlight = True

    def post_edit(self):
        self.container_selected = False
        self.border.highlight = False

    def resize(self):
        self.header.multi_set(rely=self.rely,
                              relx=self.relx + 1,
                              max_width=self.width - 1,
                              max_height=self.height)
        self.border.multi_set(rely=self.rely,
                              relx=self.relx,
                              max_width=self.width,
                              max_height=self.height)

        cur_y = self.rely + self.top_margin

        for i, widget in enumerate(self.autoables):
            widget.rely = cur_y + i
            widget.relx = self.relx + self.left_margin

    def _resize(self):
        #self.header.multi_set(rely=self.rely + 1,
                              #relx=self.relx + 1,
                              #max_width=self.width - 1,
                              #max_height=self.height)
        #self.border.multi_set(rely=self.rely,
                              #relx=self.relx,
                              #max_width=self.width,
                              #max_height=self.height)
        super(KerminalLivePlotable, self)._resize()


#These things should TOTALLY get refactored
def velocity_formatter(func, width):
    r_just = '{:>' + str(width) + '}'
    v = func()
    if v == 'None':
        return r_just.format('N/A')
    v = float(v)
    #Base units are m/s
    units = 'm/s'
    if v >= 1000.0:
        v /= 1000.0
        units = 'km/s'
    if v >= 1000.0:
        v /= 1000.0
        units = 'Mm/s'
    v = '{:.3f}'.format(v)
    return r_just.format(' '.join([v, units]))


def distance_formatter(func, width):
    r_just = '{:>' + str(width) + '}'
    a = func()
    if a == 'None':
        return r_just.format('N/A')
    a = float(func())
    units = 'm'
    if a >= 1000.0:
        a /= 1000.0
        units = 'km'
    if a >= 1000.0:
        a /= 1000.0
        units = 'Mm'
    a = '{:.3f}'.format(a)

    return r_just.format(' '.join([a, units]))


def fancy_time_formatter(func, width):
    r_just = '{:>' + str(width) + '}'
    t = func()
    if t == 'None':
        return r_just.format('N/A')
    t = float(t)
    #Kerbin-based time
    #http://wiki.kerbalspaceprogram.com/wiki/Time
    minutes, seconds = divmod(t, 60)
    hours, minutes = divmod(minutes, 60)
    days, hours = divmod(hours, 6)
    #This is weird. The KSP year is pegged to 2556.5 hours rather than a
    #precise number of days. So a year is really 426.08333... (repeating)
    years, days = divmod(days, 426.08333)
    time_str = '{:.1f}s'.format(seconds)
    if minutes:
        time_str = '{:.0f}m '.format(minutes) + time_str
    if hours:
        time_str = '{:.0f}h '.format(hours) + time_str
    if days:
        time_str = '{:.0f}d '.format(days) + time_str
    if years:
        time_str = '{:.0f}y '.format(years) + time_str

    return r_just.format(time_str)


def simple_time_formatter(func, width):
    r_just = '{:>' + str(width) + '}'
    t = func()
    if t == 'None':
        return r_just.format('N/A')
    #Much more economical with space...
    #Compare how a 1000 years looks here:   9203400000s
    #                                       2147483647
    #to just under 1000 years in the fancy: 999y 426d 5h 59m 59.9s
    t = '{:.1f}s'.format(float(t))
    return r_just.format(t)


def degree_formatter(func, width):
    r_just = '{:>' + str(width) + '}'
    d = func()
    if d == 'None':
        return r_just.format('N/A')
    #TODO: add a degree character
    d = '{:.3f}'.format(float(d))
    return r_just.format(d)


def float_formatter(func, width):
    r_just = '{:>' + str(width) + '}'
    f = func()
    if f == 'None':
        return r_just.format('N/A')
    f = '{:.3f}'.format(float(f))
    return r_just.format(f)


def plain_formatter(func, width):
    r_just = '{:>' + str(width) + '}'
    p = func()
    if p == 'None':
        p = 'N/A'
    return r_just.format(p)


def paused_formatter(func, width):
    try:
        p = int(func())
    except ValueError:
        p = None

    meanings = {0: 'Unpaused', 1: 'Paused', 2: 'No Power', 3: 'Off',
                4: 'Not Found', None: 'Not Found'}

    r_just = '{:>' + str(width) + '}'
    return r_just.format(meanings[p])


class OrbitalInfo(KerminalLivePlotable):

    #Width is sized to suit the fancy_time_formatter up to:
    #'999y 426d 5h 59m 59.9s'
    def __init__(self,
                 form,
                 parent,
                 header='Orbital Info',
                 title_length=19,
                 width=42,
                 height=10,
                 *args,
                 **kwargs):
        super(OrbitalInfo, self).__init__(form,
                                          parent,
                                          title_length=title_length,
                                          header=header,
                                          width=width,
                                          height=height,
                                          *args,
                                           **kwargs)

    def create(self):
        #widget_id, title, api-var, formatter_func
        items = [('orbitalspeed', 'Orbital Speed:', 'o.relativeVelocity',
                  velocity_formatter),
                 ('apoapsis', 'Apoapsis:', 'o.ApA', distance_formatter),
                 ('periapsis', 'Periapsis:', 'o.PeA', distance_formatter),
                 ('orbitalperiod', 'Orbital Period:', 'o.period',
                  fancy_time_formatter),
                 ('timetoapoapsis', 'Time to Apoapsis:', 'o.timeToAp',
                  fancy_time_formatter),
                 ('timetoperiapsis', 'Time to Periapsis:', 'o.timeToPe',
                  fancy_time_formatter),
                 ('inclination', 'Inclination', 'o.inclination',
                  degree_formatter),
                 ('eccentricity', 'Eccentricity', 'o.eccentricity',
                  float_formatter)]

        def get_data(data, var):
            return str(data.get(var, ''))

        f_width = self.width - (self.title_length + self.left_margin + self.right_margin + 1)

        data = self.form.parent_app.stream.data

        for key, tit, api, frmt_f in items:
            self.form.parent_app.stream.subscription_manager.add(api)
            base_func = partial(get_data, data, api)
            self.add(npyscreen2.TitledField,
                     widget_id=key,
                     field_class=SemiInteractiveText,
                     title_width=self.title_length,
                     title_value=tit,
                     field_value='',
                     field_feed=partial(frmt_f, base_func, f_width),
                     editable=False)


class SurfaceInfo(KerminalLivePlotable):

    def __init__(self,
                 form,
                 parent,
                 header='Surface Info',
                 title_length=19,
                 width=36,
                 height=10,
                 *args,
                 **kwargs):
        super(SurfaceInfo, self).__init__(form,
                                          parent,
                                          title_length=title_length,
                                          header=header,
                                          width=width,
                                          height=height,
                                          *args,
                                           **kwargs)

    def create(self):
        #widget_id, title, api-var, formatter_func
        items = [('altitudeabovesealevel', 'Altitude ASL:', 'v.altitude',
                  distance_formatter),
                 #('altitudeaboveterrain', 'Altitude True:', 'v.heightFromTerrain',
                  #distance_formatter),
                 ('surfacespeed', 'Surface Speed:', 'v.surfaceVelocity',
                  velocity_formatter),
                 ('surfacevertical', 'Vertical Speed:', 'v.verticalSpeed',
                  velocity_formatter),
                 ('pitch', 'Pitch:', 'n.pitch', degree_formatter),
                 ('heading', 'Heading:', 'n.heading', degree_formatter),
                 ('roll', 'Roll:', 'n.roll', degree_formatter),
                 ('latitude', 'Latitude:', 'v.lat', plain_formatter),
                 ('longitude', 'Longitude:', 'v.long', float_formatter),
                 ]

        def get_data(data, var):
            return str(data.get(var, ''))

        f_width = self.width - (self.title_length + self.left_margin + self.right_margin + 1)

        data = self.form.parent_app.stream.data

        for key, tit, api, frmt_f in items:
            self.form.parent_app.stream.subscription_manager.add(api)
            base_func = partial(get_data, data, api)
            self.add(npyscreen2.TitledField,
                     widget_id=key,
                     field_class=SemiInteractiveText,
                     title_width=self.title_length,
                     title_value=tit,
                     field_value='',
                     field_feed=partial(frmt_f, base_func, f_width),
                     editable=False)


class TimeInfo(KerminalLivePlotable):
    def __init__(self,
                 form,
                 parent,
                 header='Time',
                 title_length=15,
                 width=36,
                 height=4,
                 *args,
                 **kwargs):
        super(TimeInfo, self).__init__(form,
                                          parent,
                                          title_length=title_length,
                                          header=header,
                                          width=width,
                                          height=height,
                                          *args,
                                           **kwargs)

    def create(self):
        #widget_id, title, api-var, formatter_func
        items = [('mission', 'Mission Time:', 'v.missionTime',
                  fancy_time_formatter),
                 ('paused', 'Paused:', 'p.paused', paused_formatter),
                  ]

        def get_data(data, var):
            return str(data.get(var, ''))

        f_width = self.width - (self.title_length + self.left_margin + self.right_margin + 1)

        data = self.form.parent_app.stream.data

        for key, tit, api, frmt_f in items:
            self.form.parent_app.stream.subscription_manager.add(api)
            base_func = partial(get_data, data, api)
            self.add(npyscreen2.TitledField,
                     widget_id=key,
                     field_class=SemiInteractiveText,
                     title_width=self.title_length,
                     title_value=tit,
                     field_value='',
                     field_feed=partial(frmt_f, base_func, f_width),
                     editable=False)


class ResourceInfo(KerminalLivePlotable):
    #These should eventually be given gauge representations
    #Also can dynamically adjust this widget according to pertinent resource
    #types by polling Max
    def __init__(self,
                 form,
                 parent,
                 header='Resources',
                 title_length=20,
                 width=38,
                 height=20,
                 *args,
                 **kwargs):
        super(ResourceInfo, self).__init__(form,
                                          parent,
                                          title_length=title_length,
                                          header=header,
                                          width=width,
                                          height=height,
                                          *args,
                                           **kwargs)

    def create(self):
        #widget_id, title, api-var, formatter_func
        items = [('electricmax', 'Max Electric:', 'r.resourceMax[ElectricCharge]', plain_formatter),
                 ('electricurrent', 'Stage Electric:', 'r.resourceCurrent[ElectricCharge]', plain_formatter),
                 ('electrictotal', 'Total Electric:', 'r.resource[ElectricCharge]', plain_formatter),
                 ('liquidfuelmax', 'Max Liquid Fuel:', 'r.resourceMax[LiquidFuel]', plain_formatter),
                 ('liquidfuelcurrent', 'Stage Liquid Fuel:', 'r.resourceCurrent[LiquidFuel]', plain_formatter),
                 ('liquidfueltotal', 'Current Liquid Fuel:', 'r.resource[LiquidFuel]', plain_formatter),
                 ('oxidizermax', 'Max Oxidizer:', 'r.resourceMax[Oxidizer]', plain_formatter),
                 ('oxidizercurrent', 'Stage Oxidizer:', 'r.resourceCurrent[Oxidizer]', plain_formatter),
                 ('oxidizertotal', 'Total Oxidizer:', 'r.resource[Oxidizer]', plain_formatter),
                 ('monopropmax', 'Max Mono Prop.:', 'r.resourceMax[MonoPropellant]', plain_formatter),
                 ('monopropcurrent', 'Stage Mono Prop.:', 'r.resourceCurrent[MonoPropellant]', plain_formatter),
                 ('monoproptotal', 'Total Mono Prop.:', 'r.resource[MonoPropellant]', plain_formatter),
                 ('xenongasmax', 'Max Xenon Gas:', 'r.resourceMax[XenonGas]', plain_formatter),
                 ('xenongascurrent', 'Stage Xenon Gas:', 'r.resourceCurrent[XenonGas]', plain_formatter),
                 ('xenongastotal', 'Total Xenon Gas:', 'r.resource[XenonGas]', plain_formatter),
                 ('intakeairmax', 'Max Intake Air:', 'r.resourceMax[IntakeAir]', plain_formatter),
                 ('intakeaircurrent', 'Stage Intake Air:', 'r.resourceCurrent[IntakeAir]', plain_formatter),
                 ('intakeairtotal', 'Total Intake Air:', 'r.resource[IntakeAir]', plain_formatter),
                  ]

        def get_data(data, var):
            return str(data.get(var, ''))

        f_width = self.width - (self.title_length + self.left_margin + self.right_margin + 1)

        data = self.form.parent_app.stream.data

        for key, tit, api, frmt_f in items:
            self.form.parent_app.stream.subscription_manager.add(api)
            base_func = partial(get_data, data, api)
            self.add(npyscreen2.TitledField,
                     widget_id=key,
                     field_class=SemiInteractiveText,
                     title_width=self.title_length,
                     title_value=tit,
                     field_value='',
                     field_feed=partial(frmt_f, base_func, f_width),
                     editable=False)


class SensorInfo(KerminalLivePlotable):
    def __init__(self,
                 form,
                 parent,
                 header='Sensors',
                 title_length=15,
                 width=38,
                 height=6,
                 *args,
                 **kwargs):
        super(SensorInfo, self).__init__(form,
                                          parent,
                                          title_length=title_length,
                                          header=header,
                                          width=width,
                                          height=height,
                                          *args,
                                           **kwargs)

    def create(self):
        #widget_id, title, api-var, formatter_func
        items = [('temperature', 'Thermometer:', 's.sensor.temp', plain_formatter),
                 ('pressure', 'Barometer:', 's.sensor.pres', plain_formatter),
                 ('gravity', 'Grav. Detector:', 's.sensor.grav', plain_formatter),
                 ('acceleration', 'Accelerometer:', 's.sensor.acc', plain_formatter),
                  ]

        def get_data(data, var):
            return str(data.get(var, ''))

        f_width = self.width - (self.title_length + self.left_margin + self.right_margin + 1)

        data = self.form.parent_app.stream.data

        for key, tit, api, frmt_f in items:
            self.form.parent_app.stream.subscription_manager.add(api)
            base_func = partial(get_data, data, api)
            self.add(npyscreen2.TitledField,
                     widget_id=key,
                     field_class=SemiInteractiveText,
                     title_width=self.title_length,
                     title_value=tit,
                     field_value='',
                     field_feed=partial(frmt_f, base_func, f_width),
                     editable=False)