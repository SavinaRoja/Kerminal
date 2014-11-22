# encoding: utf-8

import npyscreen2
from .widgets import SemiInteractiveText
from .gauges import *
from .escape_forwarding_containers import EscapeForwardingContainer, \
                                          EscapeForwardingGridContainer

import curses
from functools import partial
import logging

log = logging.getLogger('npyscreen2.test')


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
                     value=line.rstrip())

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
                 title_bold=True,
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
                               color='Label',
                               bold=title_bold)

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


def charge_formatter(func, width):
    r_just = '{:>' + str(width) + '}'
    v = func()
    if v == 'None':
        return r_just.format('N/A')
    v = float(v)
    #Base units are Wh
    units = 'Wh'
    if v >= 1000.0:
        v /= 1000.0
        units = 'kWh'
    if v >= 1000.0:
        v /= 1000.0
        units = 'MWh'
    v = '{:.1f}'.format(v)
    return r_just.format(' '.join([v, units]))


def volume_formatter(func, width):
    r_just = '{:>' + str(width) + '}'
    v = func()
    if v == 'None':
        return r_just.format('N/A')
    elif v == '':  # MonoPropellant api string is atypical
        v = 0
    v = float(v)
    #except:
        #raise ValueError(v)
    #Base units are Wh
    units = 'L'
    if v >= 1000.0:
        v /= 1000.0
        units = 'kL'
    if v >= 1000.0:
        v /= 1000.0
        units = 'ML'
    v = '{:.1f}'.format(v)
    return r_just.format(' '.join([v, units]))


def thermometer_formatter(func, width):
    r_just = '{:>' + str(width) + '}'
    t = func()
    if t == 'None':
        return r_just.format('N/A')
    try:
        t = float(t.split(',')[1][2:-2])
    except:
        return 'debugme'
    #Base units are C
    units = 'C'
    t = '{:.2f}'.format(t)
    return r_just.format(' '.join([t, units]))


def barometer_formatter(func, width):
    r_just = '{:>' + str(width) + '}'
    p = func()
    if p == 'None':
        return r_just.format('N/A')
    try:
        p = float(p.split(',')[1][2:-2])
    except:
        return 'debugme'
    #Base units are Pa
    units = 'Pa'
    p = '{:.2f}'.format(p)
    return r_just.format(' '.join([p, units]))


def gravity_formatter(func, width):
    r_just = '{:>' + str(width) + '}'
    g = func()
    if g == 'None':
        return r_just.format('N/A')
    try:
        g = float(g.split(',')[1][2:-2])
    except:
        return 'debugme'
    #Base units are Pa
    units = 'm/s2'
    g = '{:.2f}'.format(g)
    return r_just.format(' '.join([g, units]))


def accelerometer_formatter(func, width):
    r_just = '{:>' + str(width) + '}'
    a = func()
    if a == 'None':
        return r_just.format('N/A')
    try:
        a = float(a.split(',')[1][2:-2])
    except:
        return 'debugme'
    #Base units are Pa
    units = 'Gs'
    a = '{:.2f}'.format(a)
    return r_just.format(' '.join([a, units]))


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
                 height=13,
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
                 ('rawpitch', 'Raw Pitch:', 'n.rawpitch', degree_formatter),
                 ('rawheading', 'Raw Heading:', 'n.rawheading', degree_formatter),
                 ('rawroll', 'Raw Roll:', 'n.rawroll', degree_formatter),
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
    def __init__(self,
                 form,
                 parent,
                 header='Resources',
                 title_length=20,
                 width=60,
                 height=2,
                 *args,
                 **kwargs):
        self.gauges = []
        super(ResourceInfo, self).__init__(form,
                                          parent,
                                          title_length=title_length,
                                          header=header,
                                          width=width,
                                          height=height,
                                          *args,
                                           **kwargs)

    def create(self):
        self.gauges.append(self.add(ElectricChargeGauge,
                                    widget_id='electriccharge',))
        self.gauges.append(self.add(LiquidFuelGauge,
                                    widget_id='liquidfuel',))
        self.gauges.append(self.add(LiquidFuelStageGauge,
                                    widget_id='liquidfuelstage',))
        self.gauges.append(self.add(OxidizerGauge,
                                    widget_id='oxidizerfuel',))
        self.gauges.append(self.add(OxidizerStageGauge,
                                    widget_id='oxidizerstage',))
        self.gauges.append(self.add(MonopropellantGauge,
                                    widget_id='monopropellant',))
        #self.gauges.append(self.add(MonopropellantStageGauge,  #seemed bugged
                                    #widget_id='monopropellantstage',))
        self.gauges.append(self.add(IntakeAirGauge,
                                    widget_id='intakeair',))
        self.gauges.append(self.add(XenonGasGauge,
                                    widget_id='xenongas',))

        def gauge_feed(gauge_display, data):
            if gauge_display.stage:
                value = data.get(gauge_display.api_vars['current'])
                maximum = data.get(gauge_display.api_vars['total'])
            else:
                value = data.get(gauge_display.api_vars['total'])
                maximum = data.get(gauge_display.api_vars['maximum'])
            if maximum is None:  # This really only applies to Monopropellant
                gauge_display.gauge.max_val = 1
                return 0
            if maximum == 'None' or maximum < 0:  # No capacity for the resource
                gauge_display.gauge.max_val = 1
                return 0
            else:
                gauge_display.gauge.max_val = float(maximum)
            if value == 'None':
                return 0
            value = float(value)
            return value

        def text_feed(gauge_display, data):
            if gauge_display.stage:
                value = data.get(gauge_display.api_vars['current'])
                maximum = data.get(gauge_display.api_vars['total'])
            else:
                value = data.get(gauge_display.api_vars['total'])
                maximum = data.get(gauge_display.api_vars['maximum'])
            units = gauge_display.units
            if maximum is None:  # This really only applies to Monopropellant
                gauge_display.gauge.max_val = 1
                return ' N/A '
            if maximum == 'None':
                return ' N/A '
            if value == 'None':
                value = 0
            value = float(value)
            maximum = float(maximum)
            return '{:.3e}/{:.3e} '.format(value, maximum) + units

        data = self.form.parent_app.stream.data
        sub_manager = self.form.parent_app.stream.subscription_manager

        for gauge in self.gauges:
            if not gauge.stage:
                gauge.title.bold = True
            for api_var in gauge.api_vars.values():
                sub_manager.add(api_var)
            gauge.gauge.feed = partial(gauge_feed, gauge, data)
            gauge.textvalues.feed = partial(text_feed, gauge, data)

    def resize(self):
        #Resizes itself according to contained items
        last_height = self.requested_height
        self.requested_height = (len(list(self.autoables)) + 1) * 2
        if last_height == self.requested_height:
            parent_resize = True
        else:
            parent_resize = False

        self.header.multi_set(rely=self.rely,
                              relx=self.relx + 1,
                              max_width=self.width - 1,
                              max_height=self.height)
        self.border.multi_set(rely=self.rely,
                              relx=self.relx,
                              max_width=self.width,
                              max_height=self.height)

        log = logging.getLogger('npyscreen2.test')
        log.debug('self.rely={}, self.relx={}, self.top_margin={}'.format(self.rely, self.relx, self.top_margin))
        cur_y = self.rely + self.top_margin

        for i, widget in enumerate(self.autoables):
            widget.rely = cur_y + (i * 2)
            log.debug(widget.rely)
            widget.relx = self.relx + self.left_margin

        if parent_resize:
            self.parent.resize()

    def update(self):
        log = logging.getLogger('npyscreen2.test')
        data = self.form.parent_app.stream.data
        sub_manager = self.form.parent_app.stream.subscription_manager
        made_modification = False
        for gauge in self.gauges:
            resource_max = data.get(gauge.api_vars['maximum'])
            if resource_max in [None, 'None'] or resource_max < 0:
                if gauge.live:  # Already down otherwise
                    log.debug('dismissing widget')
                    sub_manager.drop(gauge.api_vars['current'])
                    sub_manager.drop(gauge.api_vars['total'])
                    gauge.live = False
                    gauge.auto_manage = False
                    gauge.hidden = True
                    made_modification = True
            else:
                if not gauge.live:  # Already up otherwise
                    log.debug('recalling widget')
                    sub_manager.add(gauge.api_vars['current'])
                    sub_manager.add(gauge.api_vars['total'])
                    gauge.live = True
                    gauge.auto_manage = True
                    gauge.hidden = False
                    made_modification = True
        if made_modification:
            self.resize()
            self.parent._resize()


class ThrottleInfo(KerminalLivePlotable):
    def __init__(self,
                 form,
                 parent,
                 header='Throttle',
                 title_length=20,
                 width=52,
                 height=4,
                 *args,
                 **kwargs):
        super(ThrottleInfo, self).__init__(form,
                                          parent,
                                          title_length=title_length,
                                          header=header,
                                          width=width,
                                          height=height,
                                          *args,
                                           **kwargs)

    def create(self):
        #self.gauges.append(self.add(ElectricChargeGauge,
                                    #widget_id='electriccharge',
                                    #auto_manage=False))
        sub_manager = self.form.parent_app.stream.subscription_manager
        sub_manager.add('f.throttle')
        self.throttle = self.add(ThrottleGauge,
                                 widget_id='throttle',
                                 auto_manage=True,
                                 )

        def gauge_feed(gauge_display, data):
            value = data.get(gauge_display.api_vars['value'])
            if value in ['None', None]:
                return 0
            return float(value) * 100

        def text_feed(gauge_display, data):
            value = data.get(gauge_display.api_vars['value'])
            if value in ['None', None]:
                return ' N/A '
            value = float(value) * 100
            return '{:.2f}'.format(value) + gauge_display.units

        data = self.form.parent_app.stream.data

        self.throttle.gauge.feed = partial(gauge_feed,
                                           self.throttle,
                                           data)
        self.throttle.textvalues.feed = partial(text_feed,
                                                self.throttle,
                                                data)

    def resize(self):
        self.header.multi_set(rely=self.rely,
                              relx=self.relx + 1,
                              max_width=self.width - 1,
                              max_height=self.height)
        self.border.multi_set(rely=self.rely,
                              relx=self.relx,
                              max_width=self.width,
                              max_height=self.height)

        self.throttle.rely = self.rely + self.top_margin
        self.throttle.relx = self.relx + self.left_margin

        #self.throttle.multi_set()
        #cur_y = self.rely + self.top_margin

        #for i, widget in enumerate(self.autoables):
                #widget.rely = cur_y + (i * 2)
                #widget.relx = self.relx + self.left_margin

    #def update(self):
        #data = self.form.parent_app.stream.data
        #sub_manager = self.form.parent_app.stream.subscription_manager
        #made_modification = False
        #for gauge in self.gauges:
            #resource_max = data.get(gauge.api_vars['maximum'])
            #if resource_max in [None, 'None'] or resource_max < 0:
                #if gauge.live:  # Already down otherwise
                    #sub_manager.drop(gauge.api_vars['current'])
                    #sub_manager.drop(gauge.api_vars['total'])
                    #gauge.live = False
                    #gauge.auto_manage = False
                    #gauge.hidden = True
                    #made_modification = True
            #else:
                #if not gauge.live:  # Already down otherwise
                    #sub_manager.add(gauge.api_vars['current'])
                    #sub_manager.add(gauge.api_vars['total'])
                    #gauge.live = True
                    #gauge.auto_manage = True
                    #gauge.hidden = False
                    #made_modification = True
        #if made_modification:
            #self.resize()
            #self.parent._resize()


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
        items = [('temperature', 'Thermometer:', 's.sensor.temp', thermometer_formatter),
                 ('pressure', 'Barometer:', 's.sensor.pres', barometer_formatter),
                 ('gravity', 'Grav. Detector:', 's.sensor.grav', gravity_formatter),
                 ('acceleration', 'Accelerometer:', 's.sensor.acc', accelerometer_formatter),
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


class ToggleField(npyscreen2.TextField):

    def __init__(self,
                 form,
                 parent,
                 api_vars={},
                 height=1,
                 width=7,
                 state=False,
                 bold=True,
                 show_cursor=False,
                 start_cursor_at_end=False,
                 highlight_color='BUTTON_HIGHLIGHT',
                 *args,
                 **kwargs):
        self.state = state
        self.api_vars = api_vars
        super(ToggleField, self).__init__(form,
                                          parent,
                                          bold=bold,
                                          show_cursor=show_cursor,
                                          start_cursor_at_end=start_cursor_at_end,
                                          height=height,
                                          width=width,
                                          highlight_color=highlight_color,
                                          *args,
                                          **kwargs)

    def set_up_handlers(self):
        self.handlers = {curses.ascii.NL: self.h_toggle_state,
                         curses.ascii.CR: self.h_toggle_state,
                         curses.ascii.TAB: self.h_exit_ascend,
                         #curses.KEY_BTAB: self.h_exit_up,
                         curses.KEY_DOWN: self.h_exit_down,
                         curses.KEY_UP: self.h_exit_up,
                         curses.KEY_LEFT: self.h_exit_left,
                         curses.KEY_RIGHT: self.h_exit_right,
                         "^P": self.h_exit_up,
                         "^N": self.h_exit_down,
                         curses.ascii.ESC: self.h_exit_escape,
                         #curses.KEY_MOUSE: self.h_exit_mouse,
                         }
        self.complex_handlers = []

    def pre_edit(self):
        self.container_selected = True
        self.highlight = True

    def post_edit(self):
        self.container_selected = False
        self.highlight = False

    def h_toggle_state(self, inpt=None):
        stream = self.form.parent_app.stream
        if not stream.connected:
            form.error('Not connected!')
            return
        if self.state:
            self.form.info('Sending {msg_off} message'.format(**self.api_vars))
            msg_dict = {'run': [self.api_vars['send'] + '[False]']}
        else:
            self.form.info('Sending {msg_on} message'.format(**self.api_vars))
            msg_dict = {'run': [self.api_vars['send'] + '[True]']}
        stream.msg_queue.put(msg_dict)

    def update(self):
        if self.state:
            self.color = 'BUTTON'
            self.highlight_color = 'BUTTON_HIGHLIGHT'
        else:
            self.color = 'DEFAULT'
            self.highlight_color = 'HIGHLIGHT'
        super(ToggleField, self).update()


class BooleanToggles(EscapeForwardingGridContainer):

    def __init__(self,
                 form,
                 parent,
                 rows=2,
                 cols=3,
                 margin=1,
                 width=23,
                 height=4,
                 header='Buttons',
                 title_bold=True,
                 container_editable_as_widget=True,
                 *args,
                 **kwargs):
        super(BooleanToggles, self).__init__(form,
                                           parent,
                                           rows=rows,
                                           cols=cols,
                                           width=width,
                                           height=height,
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
                               color='Label',
                               bold=title_bold)

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

    def set_up_handlers(self):
        super(BooleanToggles, self).set_up_handlers()
        self.handlers.update({curses.ascii.TAB: self.h_exit_descend})

    def set_up_exit_condition_handlers(self):
        super(BooleanToggles, self).set_up_exit_condition_handlers()
        self.how_exited_handlers.update({'ascend': self.activate_container_edit,
                                         })

    def create(self):
        data = self.form.parent_app.stream.data
        sub_man = self.form.parent_app.stream.subscription_manager

        def toggle_feed(toggle, data):
            v = data.get(toggle.api_vars['status'])
            if v in [None, 'None', False, 'False']:
                toggle.state = False
            else:
                toggle.state = True
            return toggle.value

        self.rcs = self.add(ToggleField,
                            value='  RCS  ',
                            api_vars={'send': 'f.rcs',
                                      'status': 'v.rcsValue',
                                      'msg_off': 'RCS Off',
                                      'msg_on': 'RCS On'},
                            bold=True,
                            )
        sub_man.add(self.rcs.api_vars['status'])
        self.rcs.feed = partial(toggle_feed, self.rcs, data)

        self.sas = self.add(ToggleField,
                            value='  SAS  ',
                            api_vars={'send': 'f.sas',
                                      'status': 'v.sasValue',
                                      'msg_off': 'SAS Off',
                                      'msg_on': 'SAS On'},
                            bold=True,
                            )
        sub_man.add(self.sas.api_vars['status'])
        self.sas.feed = partial(toggle_feed, self.sas, data)

        self.gear = self.add(ToggleField,
                            value=' LGEAR ',
                            api_vars={'send': 'f.gear',
                                      'status': 'v.gearValue',
                                      'msg_off': 'Gear Up',
                                      'msg_on': 'Gear Down'},
                            bold=True,
                            )
        sub_man.add(self.gear.api_vars['status'])
        self.gear.feed = partial(toggle_feed, self.gear, data)

        self.light = self.add(ToggleField,
                              value=' LIGHT ',
                              api_vars={'send': 'f.light',
                                        'status': 'v.lightValue',
                                        'msg_off': 'Lights Off',
                                        'msg_on': 'Lights On'},
                              bold=True,
                              )
        sub_man.add(self.light.api_vars['status'])
        self.light.feed = partial(toggle_feed, self.light, data)

        self.brake = self.add(ToggleField,
                              value=' BRAKE ',
                              api_vars={'send': 'f.brake',
                                        'status': 'v.brakeValue',
                                        'msg_off': 'Brakes Off',
                                        'msg_on': 'Brakes On'},
                              bold=True,
                              )
        sub_man.add(self.brake.api_vars['status'])
        self.brake.feed = partial(toggle_feed, self.brake, data)

        #self.dummy = self.add(ToggleField,
                              #value='',
                              #bold=True,
                              #editable=False
                              #)

