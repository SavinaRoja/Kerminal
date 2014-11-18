# -*- coding: utf-8 -*-


from ..escape_forwarding_containers import EscapeForwardingContainer
import npyscreen2


__all__ = ['TitledGauge', 'TitledGaugeWithTextValues']


class TitledGauge(EscapeForwardingContainer):

    def __init__(self,
                 form,
                 parent,
                 title_value='',
                 title_width=None,
                 title_theme='LABEL',
                 gauge_value=0,
                 gauge_height=1,
                 gauge_width=None,
                 gauge_min_val=0,
                 gauge_max_val=100,
                 gauge_horizontal=True,
                 gauge_reverse=False,
                 gauge_theme_by_proportion=True,
                 gauge_theme_breakpoints=[],
                 gauge_themes=['DEFAULT'],
                 gauge_fill_char=' ',
                 gauge_editable=False,
                 gauge_feed=None,
                 gauge_feed_reset=False,
                 gauge_feed_reset_time=5,
                 container_editable_as_widget=True,
                 *args,
                 **kwargs):
        super(TitledGauge, self).__init__(form,
                                          parent,
                                          )

        if title_width is None:
            title_width = len(title_value) + 1

        self.title = self.add(npyscreen2.TextField,
                              color=title_theme,
                              value=title_value,
                              editable=False,
                              width=title_width,
                              auto_manage=False)

        self.gauge = self.add(npyscreen2.Gauge,
                              value=gauge_value,
                              height=gauge_height,
                              width=gauge_width,
                              min_val=gauge_min_val,
                              max_val=gauge_max_val,
                              horizontal=gauge_horizontal,
                              reverse=gauge_reverse,
                              theme_by_proportion=gauge_theme_by_proportion,
                              theme_breakpoints=gauge_theme_breakpoints,
                              themes=gauge_themes,
                              fill_char=gauge_fill_char,
                              editable=gauge_editable,
                              feed=gauge_feed,
                              feed_reset=gauge_feed_reset,
                              reset_feed_time=gauge_feed_reset_time,
                              auto_manage=False)

    def resize(self):
        self.title.multi_set(rely=self.rely + self.top_margin,
                             relx=self.relx + self.left_margin,
                             max_height=self.height - self.top_margin - self.bottom_margin,
                             max_width=self.width - self.left_margin - self.right_margin,)

        self.gauge.multi_set(rely=self.rely,
                             relx=self.relx + self.left_margin + self.title.width - 1,
                             max_height=self.height - self.left_margin - self.right_margin,
                             max_width=self.width - self.right_margin - self.title.width)


#This is a relatively experimental class, and it has me thinking about
#defining a new Container type based on proportional allocation...
#For the time being, I imagine I'll be focusing on using it in a specialized
#manner for Kerminal, but something inspired by it will almost certainly arise
#in npyscreen2
class TitledGaugeWithTextValues(TitledGauge):

    def __init__(self,
                 form,
                 parent,
                 text_width=10,
                 text_theme='LABEL',
                 text_feed=None,
                 *args,
                 **kwargs):

        super(TitledGaugeWithTextValues, self).__init__(form,
                                                        parent,
                                                        *args,
                                                        **kwargs)

        self.textvalues = self.add_widget(npyscreen2.TextField,
                                          width=text_width,
                                          editable=False,
                                          auto_manage=False,
                                          text_feed=text_feed,
                                          )

    def resize(self):
        self.title.multi_set(rely=self.rely + self.top_margin,
                             relx=self.relx + self.left_margin,
                             max_height=self.height - self.top_margin - self.bottom_margin,
                             max_width=self.width - self.left_margin - self.right_margin)

        self.textvalues.multi_set(rely=self.rely + self.top_margin,
                                  relx=self.relx + self.left_margin + self.title.width,
                                  max_height=self.height - self.top_margin - self.bottom_margin,
                                  max_width=self.width - self.left_margin - self.right_margin - self.title.width)

        self.gauge.multi_set(rely=self.rely + self.top_margin + 1,
                             relx=self.relx + self.left_margin,
                             max_height=self.height - self.top_margin - self.bottom_margin,
                             max_width=self.width - self.left_margin - self.right_margin)