#!/usr/bin/python
# -*- coding: utf-8 -*-
#####################################
# File name "trgunitdmgd.py
# Create date : 2020-3-18
# Modified date : 2020-4-11
# Author : xy
# Describe : not set
# Email : yang_31296@163.com
#from ..entitys.trigger import CTrigger
from .trigger import CTrigger


class CTriggerUnitDamaged(CTrigger):
    '''
    单元被毁伤
    '''

    def __init__(self, strGuid, mozi_server, situation):
        super().__init__(strGuid, mozi_server, situation)
        # 名称
        self.strName = ''
        # 事件触发器描述
        self.strDescription = ''
        # 事件触发器类型
        self.m_EventTriggerType = 0
        # 目标推演方GUID
        self.strTargetSide = ''
        # 目标类型
        self.m_TargetType = 0
        # 目标子类型
        self.iTargetSubType = 0
        # 目标等级
        self.iSpecificUnitClass = 0
        # 特殊单元GUID
        self.m_SpecificUnit = ''
        # 百分比阀值
        self.iDamagePercent = 0
