#!/usr/bin/python
# -*- coding: utf-8 -*-
#####################################
# File name " : zonenonav.py
# Create date : 2020-3-18
# Modified date : 2020-3-18
# Author : xy
# Describe : not set
# Email : yang_31296@163.com

#from ..entitys.zone import CZone
from .zone import CZone


class CNoNavZone(CZone):
    """
    禁航区
    """
    def __init__(self, strGuid, mozi_server, situation):
        super().__init__(strGuid,mozi_server,situation)
        # 名称
        self.strName = ''
        # 所属推演方GUID
        self.m_Side = ''
        # 区域描述
        self.strDescription = ''
        # 区域的参考点集
        self.m_AreaRefPointList = ''
        # 单元类型集合
        self.m_AffectedUnitTypes = ''
        # 是否启用
        self.bIsActive = ''
        # 是否已锁
        self.bIsLocked = ''
