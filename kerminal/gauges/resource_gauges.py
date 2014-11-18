# -*- coding: utf-8 -*-

from . import TitledGaugeWithTextValues


__all__ = ['ElectricChargeGauge', 'LiquidFuelGauge', 'LiquidFuelStageGauge',
           'OxidizerGauge', 'OxidizerStageGauge', 'MonopropellantGauge',
           'MonopropellantStageGauge', 'IntakeAirGauge', 'XenonGasGauge']


class ElectricChargeGauge(TitledGaugeWithTextValues):
    def __init__(self,
                 form,
                 parent,
                 height=2,
                 title_value='Electric Charge:',
                 text_width=22,
                 text_theme='LABEL',
                 text_feed=None,
                 units='Wh',
                 stage=False,
                 api_vars={'maximum': 'r.resourceMax[ElectricCharge]',
                           'current': 'r.resourceCurrent[ElectricCharge]',
                           'total': 'r.resource[ElectricCharge]'},
                 *args,
                 **kwargs):

        self.units = units
        self.api_vars = api_vars
        self.stage = stage

        super(ElectricChargeGauge, self).__init__(form,
                                                  parent,
                                                  height=height,
                                                  title_value=title_value,
                                                  text_width=text_width,
                                                  text_theme='LABEL',
                                                  gauge_theme_breakpoints=[0.2, 0.5],
                                                  gauge_themes=['DANGER', 'CAUTION', 'SAFE'],
                                                  *args,
                                                  **kwargs)


class LiquidFuelGauge(TitledGaugeWithTextValues):
    def __init__(self,
                 form,
                 parent,
                 height=2,
                 title_value='Liquid Fuel:',
                 text_width=22,
                 text_theme='LABEL',
                 text_feed=None,
                 units='L',
                 stage=False,
                 api_vars={'maximum': 'r.resourceMax[LiquidFuel]',
                           'current': 'r.resourceCurrent[LiquidFuel]',
                           'total': 'r.resource[LiquidFuel]'},
                 *args,
                 **kwargs):

        self.units = units
        self.api_vars = api_vars
        self.stage = stage

        super(LiquidFuelGauge, self).__init__(form,
                                              parent,
                                              height=height,
                                              title_value=title_value,
                                              text_width=text_width,
                                              text_theme='LABEL',
                                              gauge_theme_breakpoints=[0.2, 0.5],
                                              gauge_themes=['DANGER', 'CAUTION', 'SAFE'],
                                              *args,
                                              **kwargs)


class LiquidFuelStageGauge(LiquidFuelGauge):
    def __init__(self,
                 form,
                 parent,
                 stage=True,
                 title_value=' Current Stage:',
                 *args,
                 **kwargs):
        super(LiquidFuelStageGauge, self).__init__(form,
                                                   parent,
                                                   stage=stage,
                                                   title_value=title_value,
                                                   *args,
                                                   **kwargs)


class OxidizerGauge(TitledGaugeWithTextValues):
    def __init__(self,
                 form,
                 parent,
                 height=2,
                 title_value='Oxidizer:',
                 text_width=22,
                 text_theme='LABEL',
                 text_feed=None,
                 units='L',
                 stage=False,
                 api_vars={'maximum': 'r.resourceMax[Oxidizer]',
                           'current': 'r.resourceCurrent[Oxidizer]',
                           'total': 'r.resource[Oxidizer]'},
                 *args,
                 **kwargs):

        self.units = units
        self.api_vars = api_vars
        self.stage = stage

        super(OxidizerGauge, self).__init__(form,
                                              parent,
                                              height=height,
                                              title_value=title_value,
                                              text_width=text_width,
                                              text_theme='LABEL',
                                              gauge_theme_breakpoints=[0.2, 0.5],
                                              gauge_themes=['DANGER', 'CAUTION', 'SAFE'],
                                              *args,
                                              **kwargs)


class OxidizerStageGauge(OxidizerGauge):
    def __init__(self,
                 form,
                 parent,
                 stage=True,
                 title_value=' Current Stage:',
                 *args,
                 **kwargs):
        super(OxidizerStageGauge, self).__init__(form,
                                                   parent,
                                                   stage=stage,
                                                   title_value=title_value,
                                                   *args,
                                                   **kwargs)


class MonopropellantGauge(TitledGaugeWithTextValues):
    def __init__(self,
                 form,
                 parent,
                 height=2,
                 title_value='Monopropellant:',
                 text_width=22,
                 text_theme='LABEL',
                 text_feed=None,
                 units='L',
                 stage=False,
                 api_vars={'maximum': 'r.resourceMax[MonoPropellant]',
                           'current': 'r.resourceCurrent[MonoPropellant]',
                           'total': 'r.resource[MonoPropellant]'},
                 *args,
                 **kwargs):

        self.units = units
        self.api_vars = api_vars
        self.stage = stage

        super(MonopropellantGauge, self).__init__(form,
                                              parent,
                                              height=height,
                                              title_value=title_value,
                                              text_width=text_width,
                                              text_theme='LABEL',
                                              gauge_theme_breakpoints=[0.2, 0.5],
                                              gauge_themes=['DANGER', 'CAUTION', 'SAFE'],
                                              *args,
                                              **kwargs)


#There appears to be some sort of bug with this
class MonopropellantStageGauge(OxidizerGauge):
    def __init__(self,
                 form,
                 parent,
                 stage=True,
                 title_value=' Current Stage:',
                 *args,
                 **kwargs):
        super(MonopropellantStageGauge, self).__init__(form,
                                                   parent,
                                                   stage=stage,
                                                   title_value=title_value,
                                                   *args,
                                                   **kwargs)


class IntakeAirGauge(TitledGaugeWithTextValues):
    def __init__(self,
                 form,
                 parent,
                 height=2,
                 title_value='Intake Air:',
                 text_width=22,
                 text_theme='LABEL',
                 text_feed=None,
                 units='L',
                 stage=False,
                 api_vars={'maximum': 'r.resourceMax[IntakeAir]',
                           'current': 'r.resourceCurrent[IntakeAir]',
                           'total': 'r.resource[IntakeAir]'},
                 *args,
                 **kwargs):

        self.units = units
        self.api_vars = api_vars
        self.stage = stage

        super(IntakeAirGauge, self).__init__(form,
                                              parent,
                                              height=height,
                                              title_value=title_value,
                                              text_width=text_width,
                                              text_theme='LABEL',
                                              gauge_theme_breakpoints=[0.2, 0.5],
                                              gauge_themes=['DANGER', 'CAUTION', 'SAFE'],
                                              *args,
                                              **kwargs)


class XenonGasGauge(TitledGaugeWithTextValues):
    def __init__(self,
                 form,
                 parent,
                 height=2,
                 title_value='Xenon Gas:',
                 text_width=22,
                 text_theme='LABEL',
                 text_feed=None,
                 units='hg',
                 stage=False,
                 api_vars={'maximum': 'r.resourceMax[XenonGas]',
                           'current': 'r.resourceCurrent[XenonGas]',
                           'total': 'r.resource[XenonGas]'},
                 *args,
                 **kwargs):

        self.units = units
        self.api_vars = api_vars
        self.stage = stage

        super(XenonGasGauge, self).__init__(form,
                                              parent,
                                              height=height,
                                              title_value=title_value,
                                              text_width=text_width,
                                              text_theme='LABEL',
                                              gauge_theme_breakpoints=[0.2, 0.5],
                                              gauge_themes=['DANGER', 'CAUTION', 'SAFE'],
                                              *args,
                                              **kwargs)