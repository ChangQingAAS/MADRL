# 时间 ： 2020/8/15 20:16
# 作者 ： Dixit
# 文件 ： actions.py
# 项目 ： moziAIBT2
# 版权 ： 北京华戍防务技术有限公司

from mozi_ai_sdk.btmodel.bt import utils
import re
import random
from mozi_simu_sdk.mssnpatrol import CPatrolMission
from mozi_simu_sdk.mssnsupport import CSupportMission
from mozi_ai_sdk.btmodel.bt.basic import *
from mozi_ai_sdk.btmodel.bt.detail import *

import geopy
from geopy import distance
from math import radians, cos, sin, asin, sqrt, degrees, atan2, degrees


def situationAwareness(scenario):
    redside = scenario.get_side_by_name('红方')
    contacts = redside.contacts
    mssnSitu = redside.strikemssns
    patrolmssn = redside.patrolmssns
    # targets = {k: v for k, v in contacts.items() if (('DDG' in v.strName) | ('CVN' in v.strName))}
    target = {k: v for k, v in contacts.items() if ('DDG' in v.strName)}
    if len(target) == 0:
        return False
    strkmssn = [v for v in mssnSitu.values() if v.strName == 'strike2'][0]
    strkPatrol = [v for v in patrolmssn.values() if v.strName == 'strikePatrol']

    # 获取任务执行单元
    missionUnits = strkmssn.m_AssignedUnits.split('@')
    create = False
    for unitGuid in missionUnits:
        check_unit_retreat_and_compute_retreat_pos(redside, unitGuid)

        # TODO 切换任务
        # retreat, retreatPos = utils.check_unit_retreat_and_compute_retreat_pos(redside, unitGuid)
        # if retreat == True:
        #     if len(strkPatrol) == 0 & create == False:
        #         pos = {}
        #         pos['latitude'] = list(target.values())[0].dLatitude
        #         pos['longitude'] = list(target.values())[0].dLongitude
        #         point_list = utils.create_patrol_zone(redside, pos)
        #         postr = []
        #         for point in point_list:
        #             postr.append(point.strName)
        #         redside.add_mission_patrol('strikePatrol', 1, postr)
        #         strikePatrolmssn = CPatrolMission('T+1_mode', scenario.mozi_server, scenario.situation)
        #         strikePatrolmssn.strName = 'strikePatrol'
        #         # 取消满足编队规模才能起飞的限制（任务条令）
        #         strikePatrolmssn.set_flight_size_check('红方', 'strikePatrol', 'false')
        #         utils.change_unit_mission(redside, strkmssn, strikePatrolmssn, missionUnits)
        #         return True
        #     else:
        #         break


def check_unit_retreat_and_compute_retreat_pos(side, unit_guid):
    """

    :param side: 方
    :param unit_guid: 单元guid
    :return:
    """
    contacts = side.contacts
    # miss_dic = side.missions
    airs_dic = side.aircrafts
    AirContacts = get_air_contacts(contacts)
    unit = None
    for k, v in airs_dic.items():
        if k == unit_guid:
            unit = v
            break
    unitPos = {}
    if unit == None:
        return None, None
    else:
        unitPos['Latitude'] = unit.dLatitude
        unitPos['Longitude'] = unit.dLongitude

    for k, v in AirContacts.items():
        if v.m_IdentificationStatus >= 3:
            disKilo = get_two_point_distance(unitPos['Longitude'], unitPos['Latitude'], v.dLongitude,
                                             v.dLatitude)
            if disKilo <= v.fAirRangeMax * 1.852:  # 海里转公里需要乘以1.852
                # 计算撤退点 TODO
                doctrine = unit.get_doctrine()
                doctrine.ignore_plotted_course('yes')
                unit.set_unit_heading(unit.fCurrentHeading + 180)
                retreatPos = get_point_with_point_bearing_distance(unitPos['Longitude'], unitPos['Latitude'],
                                                                   unit.fCurrentHeading + 180, 10)
                unit.plot_course([retreatPos])

                return True, retreatPos
        else:
            continue
    return False, None


def get_point_with_point_bearing_distance(lat, lon, bearing, distance):
    """
    一直一点求沿某一方向一段距离的点
    :param lat:纬度
    :param lon:经度
    :param bearing:朝向角
    :param distance:距离
    :return:
    """
    # pylog.info("lat:%s lon:%s bearing:%s distance:%s" % (lat, lon, bearing, distance))
    radiusEarthKilometres = 3440
    initialBearingRadians = radians(bearing)
    disRatio = distance / radiusEarthKilometres
    distRatioSine = sin(disRatio)
    distRatioCosine = cos(disRatio)
    startLatRad = radians(lat)
    startLonRad = radians(lon)
    startLatCos = cos(startLatRad)
    startLatSin = sin(startLatRad)
    endLatRads = asin((startLatSin * distRatioCosine) + (startLatCos * distRatioSine * cos(initialBearingRadians)))
    endLonRads = startLonRad + atan2(sin(initialBearingRadians) * distRatioSine * startLatCos,
                                     distRatioCosine - startLatSin * sin(endLatRads))
    my_lat = degrees(endLatRads)
    my_lon = degrees(endLonRads)
    # dic = {"latitude": my_lat, "longitude": my_lon}
    # dic = tuple(my_lat, my_lon)
    return my_lat, my_lon


def get_distance_point(lat, lon, dis, direction):
    """
    根据经纬度，距离，方向获得一个地点
    :param lat: 纬度
    :param lon: 经度
    :param dis: 距离（千米）
    :param direction: 方向（北：0，东：90，南：180，西：360）
    :return:
    """
    start = geopy.Point(lat, lon)
    d = distance.VincentyDistance(kilometers=dis)
    d = d.destination(point=start, bearing=direction)
    print(d.latitude, d.longitude)
    dic = {"latitude": d.latitude, "longitude": d.longitude}
    return dic


# print(get_distance_point(33.0625105185452, 44.6287913650984, 40, 325))
# latitude='33.3681951159897', longitude='44.3768440602801'

# def get_two_point_distance(lon1, lat1, lon2, lat2):
#     pos1 = (lat1, lon1)
#     pos2 = (lat2, lon2)
#     dis = distance.vincenty(pos1, pos2)
#     return dis.kilometers

def get_two_point_distance(lat1, lon1, lat2,lon2):
    pos1 = (lat1, lon1)
    pos2 = (lat2, lon2)
    dis = distance.vincenty(pos1, pos2)
    return dis.kilometers


def MakeLatLong(latitude, longitude):
    instance = {'latitude': InternationalDecimalConverter(latitude),
                'longitude': InternationalDecimalConverter(longitude)}
    return instance


# 三维地球上两点中间的坐标
def MidPointCoordinate(lat1, lon1, lat2, lon2):
    # initialize
    lat1 = InternationalDecimalConverter(lat1)
    lon1 = InternationalDecimalConverter(lon1)
    lat2 = InternationalDecimalConverter(lat2)
    lon2 = InternationalDecimalConverter(lon2)
    dLon = math.radians(lon2 - lon1)
    # convert to radians
    lat1 = math.radians(lat1)
    lat2 = math.radians(lat2)
    lon1 = math.radians(lon1)

    Bx = math.cos(lat2) * math.cos(dLon)
    By = math.cos(lat2) * math.sin(dLon)
    lat3 = math.atan2(math.sin(lat1) + math.sin(lat2),
                      math.sqrt((math.cos(lat1) + Bx) * (math.cos(lat1) + Bx) + By * By))
    lon3 = lon1 + math.atan2(By, math.cos(lat1) + Bx)

    return MakeLatLong(math.degrees(lat3), math.degrees(lon3))


def get_air_contacts(contacts):
    AirContacts = {}
    for k, v in contacts.items():
        if v.m_ContactType == 0:
            AirContacts[k] = v
    return AirContacts


def FindBoundingBoxForGivenContacts(contacts, defaults, padding):
    #  Variables
    coordinates = [btBas.MakeLatLong(defaults['AI-AO-1']['latitude'], defaults['AI-AO-1']['longitude']),
                   btBas.MakeLatLong(defaults['AI-AO-2']['latitude'], defaults['AI-AO-2']['longitude']),
                   btBas.MakeLatLong(defaults['AI-AO-3']['latitude'], defaults['AI-AO-3']['longitude']),
                   btBas.MakeLatLong(defaults['AI-AO-4']['latitude'], defaults['AI-AO-4']['longitude'])]
    contactBoundingBox = FindBoundingBoxForGivenLocations(coordinates, padding)
    contactCoordinates = []

    for k, v in contacts.items():
        contact = {'latitude': v.dLatitude, 'longitude': v.dLongitude}
        contactCoordinates.append(btBas.MakeLatLong(contact['latitude'], contact['longitude']))

    # Get Hostile Contact Bounding Box
    if len(contactCoordinates) > 0:
        contactBoundingBox = FindBoundingBoxForGivenLocations(contactCoordinates, padding)

    # Return Bounding Box
    return contactBoundingBox


def FindBoundingBoxForGivenLocations(coordinates, padding):
    west = 0.0
    east = 0.0
    north = 0.0
    south = 0.0

    # conditions Check
    if coordinates is None or len(coordinates) == 0:
        padding = 0

    # Assign Up to numberOfReconToAssign
    for lc in range(0, len(coordinates)):
        loc = coordinates[lc]
        if lc == 0:
            north = loc['latitude']
            south = loc['latitude']
            west = loc['longitude']
            east = loc['longitude']
        else:
            if loc['latitude'] > north:
                north = loc['latitude']
            elif loc['latitude'] < south:
                south = loc['latitude']

            if loc['longitude'] < west:
                west = loc['longitude']
            elif loc['longitude'] > east:
                east = loc['longitude']

    # Adding Padding
    north = north + padding
    south = south - padding
    west = west - padding
    east = east + padding

    # Return In Format
    return [MakeLatLong(north, west), MakeLatLong(north, east), MakeLatLong(south, east), MakeLatLong(south, west)]


# a1_aaw_miss_1
def AttackDoctrineCreateAirMissionAction(scenario):
    side = scenario.get_side_by_name('蓝方')
    defaultRef = ['AI-AO-1', 'AI-AO-2', 'AI-AO-3', 'AI-AO-4']
    defaults = {v.strName: {'latitude': v.dLatitude, 'longitude': v.dLongitude} for k, v in side.referencepnts.items()
                if v.strName in defaultRef}
    airContacts_dic = {k: v for k, v in side.contacts.items() if v.m_ContactType == 0}  # 探测到的敌方飞机
    airs_dic = side.aircrafts  # 本方所有飞机
    patrolmssn = [v for _, v in side.patrolmssns.items() if v.strName == 'a1_aaw_miss_1']
    if len(patrolmssn) == 1 or len(airs_dic) == 0 or len(airContacts_dic) == 0:
        return False

    hostileContactBoundingBox = FindBoundingBoxForGivenContacts(airContacts_dic, defaults, 10)
    zone = ['a1_aaw_miss_1_rp_1', 'a1_aaw_miss_1_rp_2', 'a1_aaw_miss_1_rp_3', 'a1_aaw_miss_1_rp_4']
    side.add_reference_point('蓝方', zone[0], hostileContactBoundingBox[0][0], hostileContactBoundingBox[0][1])
    side.add_reference_point('蓝方', zone[1], hostileContactBoundingBox[1][0], hostileContactBoundingBox[1][1])
    side.add_reference_point('蓝方', zone[2], hostileContactBoundingBox[2][0], hostileContactBoundingBox[2][1])
    side.add_reference_point('蓝方', zone[3], hostileContactBoundingBox[3][0], hostileContactBoundingBox[3][1])

    side.add_mission_patrol('a1_aaw_miss_1', 0, zone)  # 空战巡逻
    a1_aaw_miss = CPatrolMission('T+1_mode', scenario.mozi_server, scenario.situation)
    a1_aaw_miss.strName = 'a1_aaw_miss_1'
    # 取消满足编队规模才能起飞的限制（任务条令）
    a1_aaw_miss.set_flight_size_check('蓝方', 'a1_aaw_miss_1', True)
    a1_aaw_miss.set_one_third_rule('蓝方', 'a1_aaw_miss_1', False)
    a1_aaw_miss.set_opa_check('蓝方', 'a1_aaw_miss_1', False)
    a1_aaw_miss.set_wwr_check('蓝方', 'a1_aaw_miss_1', True)

    missionUnits = {k: v for k, v in airs_dic.items() if int(re.sub('\D', '', v.strName)) <= 5}
    a1_aaw_miss.assign_units(missionUnits)

    return True


def AttackDoctrineUpdateAirMissionAction(scenario):
    side = scenario.get_side_by_name('蓝方')
    defaultRef = ['AI-AO-1', 'AI-AO-2', 'AI-AO-3', 'AI-AO-4']
    defaults = {v.strName: {'latitude': v.dLatitude, 'longitude': v.dLongitude} for k, v in side.referencepnts.items()
                if v.strName in defaultRef}
    airContacts_dic = {k: v for k, v in side.contacts.items() if v.m_ContactType == 0}  # 探测到的敌方飞机
    airs_dic = side.aircrafts  # 本方所有飞机
    patrolmssn = [v for _, v in side.patrolmssns.items() if v.strName == 'a1_aaw_miss_1']
    if len(patrolmssn) == 0 or len(airs_dic) == 0:
        return False

    hostileContactBoundingBox = FindBoundingBoxForGivenContacts(airContacts_dic, defaults, 3)
    zone = ['a1_aaw_miss_1_rp_1', 'a1_aaw_miss_1_rp_2', 'a1_aaw_miss_1_rp_3', 'a1_aaw_miss_1_rp_4']

    set_str_1 = "ScenEdit_SetReferencePoint({{side='{}',guid='{}', lat={}, lon={}}})".format(
        '蓝方', zone[0], hostileContactBoundingBox[0][0], hostileContactBoundingBox[0][1])
    scenario.mozi_server.send_and_recv(set_str_1)
    set_str_2 = "ScenEdit_SetReferencePoint({{side='{}',guid='{}', lat={}, lon={}}})".format(
        '蓝方', zone[1], hostileContactBoundingBox[1][0], hostileContactBoundingBox[1][1])
    scenario.mozi_server.send_and_recv(set_str_2)
    set_str_3 = "ScenEdit_SetReferencePoint({{side='{}',guid='{}', lat={}, lon={}}})".format(
        '蓝方', zone[2], hostileContactBoundingBox[2][0], hostileContactBoundingBox[2][1])
    scenario.mozi_server.send_and_recv(set_str_3)
    set_str_4 = "ScenEdit_SetReferencePoint({{side='{}',guid='{}', lat={}, lon={}}})".format(
        '蓝方', zone[3], hostileContactBoundingBox[3][0], hostileContactBoundingBox[3][1])
    scenario.mozi_server.send_and_recv(set_str_4)

    return True


# a1_aaew_miss_1
def AttackDoctrineCreateAEWMissionAction(scenario):
    side = scenario.get_side_by_name('蓝方')
    defaultRef = ['a1_aaw_miss_1_rp_1', 'a1_aaw_miss_1_rp_2', 'a1_aaw_miss_1_rp_3', 'a1_aaw_miss_1_rp_4']
    linkedMissionPoints = {v.strName: {'latitude': v.dLatitude, 'longitude': v.dLongitude} for k, v in
                           side.referencepnts.items()
                           if v.strName in defaultRef}
    airContacts_dic = {k: v for k, v in side.contacts.items() if v.m_ContactType == 0}  # 探测到的敌方飞机
    airs_dic = side.aircrafts  # 本方所有飞机
    supportmssn = [v for _, v in side.supportmssns.items() if v.strName == 'a1_aaew_miss_1']
    if len(supportmssn) == 1 or len(linkedMissionPoints) == 0 or len(airs_dic) == 0 or len(airContacts_dic) == 0:
        return False

    linkedMissionCenterPoint = MidPointCoordinate(linkedMissionPoints['a1_aaw_miss_1_rp_1']['latitude'],
                                                  linkedMissionPoints['a1_aaw_miss_1_rp_1']['longitude'],
                                                  linkedMissionPoints['a1_aaw_miss_1_rp_3']['latitude'],
                                                  linkedMissionPoints['a1_aaw_miss_1_rp_3']['longitude'])
    patrolBoundingBox = FindBoundingBoxForGivenLocations(
        [MakeLatLong(linkedMissionCenterPoint['latitude'], linkedMissionCenterPoint['longitude'])], 1.0)
    zone = ['a1_aaew_miss_1_rp_1', 'a1_aaew_miss_1_rp_2', 'a1_aaew_miss_1_rp_3', 'a1_aaew_miss_1_rp_4']
    # side.add_reference_point('蓝方', zone[0], patrolBoundingBox[0][0], patrolBoundingBox[0][1])
    # side.add_reference_point('蓝方', zone[1], patrolBoundingBox[1][0], patrolBoundingBox[1][1])
    # side.add_reference_point('蓝方', zone[2], patrolBoundingBox[2][0], patrolBoundingBox[2][1])
    # side.add_reference_point('蓝方', zone[3], patrolBoundingBox[3][0], patrolBoundingBox[3][1])
    side.add_reference_point(zone[0], patrolBoundingBox[0][0], patrolBoundingBox[0][1])
    side.add_reference_point(zone[1], patrolBoundingBox[1][0], patrolBoundingBox[1][1])
    side.add_reference_point(zone[2], patrolBoundingBox[2][0], patrolBoundingBox[2][1])
    side.add_reference_point(zone[3], patrolBoundingBox[3][0], patrolBoundingBox[3][1])

    side.add_mission_support('a1_aaew_miss_1', zone)  # 支援任务
    a1_aaew_miss = CSupportMission('T+1_mode', scenario.mozi_server, scenario.situation)
    a1_aaew_miss.strName = 'a1_aaew_miss_1'
    # 取消满足编队规模才能起飞的限制（任务条令）
    a1_aaew_miss.set_flight_size_check('蓝方', 'a1_aaw_miss_1', True)
    a1_aaew_miss.set_one_third_rule('蓝方', 'a1_aaw_miss_1', False)
    a1_aaew_miss.set_opa_check('蓝方', 'a1_aaw_miss_1', False)
    a1_aaew_miss.set_wwr_check('蓝方', 'a1_aaw_miss_1', True)

    missionUnits = {k: v for k, v in airs_dic.items() if int(re.sub('\D', '', v.strName)) <= 5}
    a1_aaew_miss.assign_units(missionUnits)


def AttackDoctrineUpdateAEWAirMissionAction(scenario):
    side = scenario.get_side_by_name('蓝方')
    defaultRef = ['a1_aaw_miss_1_rp_1', 'a1_aaw_miss_1_rp_2', 'a1_aaw_miss_1_rp_3', 'a1_aaw_miss_1_rp_4']
    linkedMissionPoints = {v.strName: {'latitude': v.dLatitude, 'longitude': v.dLongitude} for k, v in
                           side.referencepnts.items()
                           if v.strName in defaultRef}
    airs_dic = side.aircrafts  # 本方所有飞机
    supportmssn = [v for _, v in side.supportmssns.items() if v.strName == 'a1_aaew_miss_1']
    if len(supportmssn) == 1 or len(linkedMissionPoints) == 0 or len(airs_dic) == 0:
        return False

    linkedMissionCenterPoint = MidPointCoordinate(linkedMissionPoints['a1_aaw_miss_1_rp_1']['latitude'],
                                                  linkedMissionPoints['a1_aaw_miss_1_rp_1']['longitude'],
                                                  linkedMissionPoints['a1_aaw_miss_1_rp_3']['latitude'],
                                                  linkedMissionPoints['a1_aaw_miss_1_rp_3']['longitude'])
    patrolBoundingBox = FindBoundingBoxForGivenLocations(
        [MakeLatLong(linkedMissionCenterPoint['latitude'], linkedMissionCenterPoint['longitude'])], 1.0)
    zone = ['a1_aaew_miss_1_rp_1', 'a1_aaew_miss_1_rp_2', 'a1_aaew_miss_1_rp_3', 'a1_aaew_miss_1_rp_4']

    set_str_1 = "ScenEdit_SetReferencePoint({{side='{}',guid='{}', lat={}, lon={}}})".format(
        '蓝方', zone[0], patrolBoundingBox[0][0], patrolBoundingBox[0][1])
    scenario.mozi_server.send_and_recv(set_str_1)
    set_str_2 = "ScenEdit_SetReferencePoint({{side='{}',guid='{}', lat={}, lon={}}})".format(
        '蓝方', zone[1], patrolBoundingBox[1][0], patrolBoundingBox[1][1])
    scenario.mozi_server.send_and_recv(set_str_2)
    set_str_3 = "ScenEdit_SetReferencePoint({{side='{}',guid='{}', lat={}, lon={}}})".format(
        '蓝方', zone[2], patrolBoundingBox[2][0], patrolBoundingBox[2][1])
    scenario.mozi_server.send_and_recv(set_str_3)
    set_str_4 = "ScenEdit_SetReferencePoint({{side='{}',guid='{}', lat={}, lon={}}})".format(
        '蓝方', zone[3], patrolBoundingBox[3][0], patrolBoundingBox[3][1])
    scenario.mozi_server.send_and_recv(set_str_4)


# saaw_miss
def AttackDoctrineCreateStealthAirMissionAction(scenario):
    side = scenario.get_side_by_name('蓝方')


def AttackDoctrineUpdateStealthAirMissionAction(scenario):
    side = scenario.get_side_by_name('蓝方')


# aew_sup_miss
def SupportAEWDoctrineCreateMissionAction(scenario):
    side = scenario.get_side_by_name('蓝方')
    missions = side.get_patrol_missions()
    aew_missions = [mission for mission in missions.values() if 'aew_sup_miss' in mission.strName]
    defaultRef = ['AI-AO-1', 'AI-AO-2', 'AI-AO-3', 'AI-AO-4']
    defaults = {v.strName: {'latitude': v.dLatitude, 'longitude': v.dLongitude} for k, v in side.referencepnts.items()
                if v.strName in defaultRef}
    key_order = sorted(defaults.keys())
    aoPoints = [defaults[key] for key in key_order]
    totalFreeBusyInventory = side.aircrafts
    # TODO AEW的飞机
    AEWInvertory = {k: v for k, v in totalFreeBusyInventory.items() if '预警机' in v.strName}

    totalHostileContacts = side.contacts
    totalHostilesInZone = 0
    unitToSupport = None
    updatedMission = None

    totalHVTs = {}
    coveredHVTs = {}

    if len(coveredHVTs) >= len(totalHVTs) or len(AEWInvertory) == 0:
        return False
    for k, v in totalHVTs.items():
        found = False
        for m, n in coveredHVTs.items():
            if v == n:
                found = True
        if not found:
            unitToSupport = v
            break
    if not unitToSupport:
        return False
    coor = MakeLatLong(unitToSupport.latitude, unitToSupport.longitude)
    defenseBoundingBox = FindBoundingBoxForGivenLocations(coor, 1)

    rp1 = side.add_reference_point('rp1', defenseBoundingBox[1].latitude, defenseBoundingBox[1].longitude)
    rp2 = side.add_reference_point('rp2', defenseBoundingBox[2].latitude, defenseBoundingBox[2].longitude)
    rp3 = side.add_reference_point('rp3', defenseBoundingBox[3].latitude, defenseBoundingBox[3].longitude)
    rp4 = side.add_reference_point('rp4', defenseBoundingBox[4].latitude, defenseBoundingBox[4].longitude)
    point_list = [rp1, rp2, rp3, rp4]
    point_str = []
    for point in point_list:
        point_str.append(point.strName)
    patrol_name = 'a1_aew_sup_miss_' + unitToSupport.strGuid

    side.add_mission_patrol(patrol_name, 0, point_str)
    suppmssn = CSupportMission('T+1_mode', scenario.mozi_server, scenario.situation)
    suppmssn.strName = patrol_name
    suppmssn.switch_radar('true')
    suppmssn.assign_units(AEWInvertory)


def SupportAEWDoctrineUpdateMissionAction(scenario):
    side = scenario.get_side_by_name('蓝方')
    missions = side.get_patrol_missions()
    aew_missions = [mission for mission in missions.values() if 'aew_sup_miss' in mission.strName]
    defaultRef = ['AI-AO-1', 'AI-AO-2', 'AI-AO-3', 'AI-AO-4']
    defaults = {v.strName: {'latitude': v.dLatitude, 'longitude': v.dLongitude} for k, v in side.referencepnts.items()
                if v.strName in defaultRef}
    key_order = sorted(defaults.keys())
    aoPoints = [defaults[key] for key in key_order]
    # totalFreeBusyInventory 包含的飞机：TotalFreeBusyReconInventory，FreeBusyAirStealthFighterInventory

    totalFreeBusyInventory = side.aircrafts
    # TODO AEW的飞机
    # AEWInvertory = totalFreeBusyInventory()
    totalHostileContacts = side.contacts
    totalHostilesInZone = 0
    updatedMission = None

    # 高价值目标
    totalHVTs = {}
    coveredHVTs = {}

    if len(aew_missions) == 0:
        return False
    for k, v in coveredHVTs.items():
        # coveredHVT =
        pass


# aaw_d_miss
def DefendDoctrineCreateAirMissionAction(scenario):
    side = scenario.get_side_by_name('蓝方')
    return False


def DefendDoctrineUpdateAirMissionAction(scenario):
    side = scenario.get_side_by_name('蓝方')
    return False


# 巡逻区域经纬度的生成
def create_patrol_zone(scenario, aoPoints, missionNumber):
    side = scenario.get_side_by_name('蓝方')
    # 生成大四边形的四个中点
    rp12mid = MidPointCoordinate(aoPoints[1].latitude, aoPoints[1].longitude, aoPoints[2].latitude,
                                 aoPoints[2].longitude)
    rp13mid = MidPointCoordinate(aoPoints[1].latitude, aoPoints[1].longitude, aoPoints[3].latitude,
                                 aoPoints[3].longitude)
    rp14mid = MidPointCoordinate(aoPoints[1].latitude, aoPoints[1].longitude, aoPoints[4].latitude,
                                 aoPoints[4].longitude)
    rp23mid = MidPointCoordinate(aoPoints[2].latitude, aoPoints[2].longitude, aoPoints[3].latitude,
                                 aoPoints[3].longitude)
    rp34mid = MidPointCoordinate(aoPoints[3].latitude, aoPoints[3].longitude, aoPoints[4].latitude,
                                 aoPoints[4].longitude)
    # 如果是rec巡逻任务1，添加4个参考点：rp1，rp2，rp3，rp4
    if missionNumber == 1:
        # lat: 纬度， lon：经度
        rp1 = side.add_reference_point('rp1', aoPoints[1].latitude, aoPoints[1].longitude)
        rp2 = side.add_reference_point('rp2', rp12mid.latitude, rp12mid.longitude)
        rp3 = side.add_reference_point('rp3', rp13mid.latitude, rp13mid.longitude)
        rp4 = side.add_reference_point('rp4', rp14mid.latitude, rp14mid.longitude)

    elif missionNumber == 2:
        rp1 = side.add_reference_point('rp1', rp12mid.latitude, rp12mid.longitude)
        rp2 = side.add_reference_point('rp2', aoPoints[2].latitude, aoPoints[2].longitude)
        rp3 = side.add_reference_point('rp3', rp23mid.latitude, rp23mid.longitude)
        rp4 = side.add_reference_point('rp4', rp13mid.latitude, rp13mid.longitude)

    elif missionNumber == 3:
        rp1 = side.add_reference_point('rp1', rp13mid.latitude, rp13mid.longitude)
        rp2 = side.add_reference_point('rp2', rp23mid.latitude, rp23mid.longitude)
        rp3 = side.add_reference_point('rp3', aoPoints[3].latitude, aoPoints[3].longitudel)
        rp4 = side.add_reference_point('rp4', rp34mid.latitude, rp34mid.longitude)
    else:
        rp1 = side.add_reference_point('rp1', rp14mid.latitude, rp14mid.longitude)
        rp2 = side.add_reference_point('rp2', rp13mid.latitude, rp13mid.longitude)
        rp3 = side.add_reference_point('rp3', rp34mid.latitude, rp34mid.longitude)
        rp4 = side.add_reference_point('rp4', aoPoints[4].latitude, aoPoints[4].longitude)
    return [rp1, rp2, rp3, rp4]


def ReconDoctrineCreateMissionAction(scenario):
    side = scenario.get_side_by_name('蓝方')
    defaultRef = ['AI-AO-1', 'AI-AO-2', 'AI-AO-3', 'AI-AO-4']
    defaults = {v.strName: {'latitude': v.dLatitude, 'longitude': v.dLongitude} for k, v in side.referencepnts.items()
                if v.strName in defaultRef}
    key_order = sorted(defaults.keys())
    aoPoints = [defaults[key] for key in key_order]
    airs = side.aircrafts
    recon_airs = [air for air in airs.values() if 'F-35' in air.strName]
    missions = side.get_patrol_missions()
    recon_missions = [mission for mission in missions.values() if 'rec_miss' in mission.strName]
    missionNumber = random.randint(1, 4)
    recon_mission_name = [mission.strName for mission in recon_missions]
    for mission in recon_missions:
        if str(missionNumber) in mission.strName:
            missionNumber = random.randint(1, 4)

    if (len(recon_missions) >= 4) or (len(recon_airs) == 0) or (side.contacts >= 10):
        return False
    point_list = create_patrol_zone(scenario, aoPoints, missionNumber)
    point_str = []
    for point in point_list:
        point_str.append(point.strName)
    patrol_name = 'a1_rec_miss' + str(missionNumber)
    if patrol_name in recon_mission_name:
        return False
    side.add_mission_patrol(patrol_name, 0, point_str)
    patrolmssn = CPatrolMission('T+1_mode', scenario.mozi_server, scenario.situation)
    patrolmssn.strName = patrol_name
    patrolmssn.set_opa_check('false')
    patrolmssn.set_wwr_check('true')

    # 设置条令
    recon_doctrine = patrolmssn.get_doctrine()
    recon_doctrine.evade_automatically('yes')
    recon_doctrine.maintain_standoff('yes')
    recon_doctrine.ignore_emcon_while_under_attack('yes')

    recon_doctrine.set_weapon_state_for_aircraft('5001')
    recon_doctrine.set_weapon_state_for_air_group('0')
    recon_doctrine.dive_on_threat('2')
    recon_doctrine.set_em_control_status('Radar', 'Passive')

    # 分配飞机给任务
    recon_air = recon_airs[missionNumber]
    patrolmssn.assign_units(recon_air)


def ReconDoctrineUpdateMissionAction(scenario):
    side = scenario.get_side_by_name('蓝方')
    missions = side.get_patrol_missions()
    recon_missions = [mission for mission in missions.values() if 'rec_miss' in mission.strName]
    # totalFreeBusyInventory 包含的飞机：TotalFreeBusyReconInventory，FreeBusyAirStealthFighterInventory
    totalFreeBusyInventory = side.aircrafts

    missionNumber = 0

    defaultRef = ['AI-AO-1', 'AI-AO-2', 'AI-AO-3', 'AI-AO-4']
    defaults = {v.strName: {'latitude': v.dLatitude, 'longitude': v.dLongitude} for k, v in side.referencepnts.items()
                if v.strName in defaultRef}
    key_order = sorted(defaults.keys())
    aoPoints = [defaults[key] for key in key_order]

    # aoPoints = get_reference_point(scenario, 'AI-AO-1', 'AI-AO-2', 'AI-AO-3', 'AI-AO-4')
    if len(totalFreeBusyInventory) == 0:
        return False
    # Loop Through Existing Missions
    for mission in recon_missions:
        missionNumber = missionNumber + 1
        # Update Reference Points (AO Change)
        rp12mid = MidPointCoordinate(aoPoints[1].latitude, aoPoints[1].longitude, aoPoints[2].latitude,
                                     aoPoints[2].longitude)
        rp13mid = MidPointCoordinate(aoPoints[1].latitude, aoPoints[1].longitude, aoPoints[3].latitude,
                                     aoPoints[3].longitude)
        rp14mid = MidPointCoordinate(aoPoints[1].latitude, aoPoints[1].longitude, aoPoints[4].latitude,
                                     aoPoints[4].longitude)
        rp23mid = MidPointCoordinate(aoPoints[2].latitude, aoPoints[2].longitude, aoPoints[3].latitude,
                                     aoPoints[3].longitude)
        rp34mid = MidPointCoordinate(aoPoints[3].latitude, aoPoints[3].longitude, aoPoints[4].latitude,
                                     aoPoints[4].longitude)
        rp = ["_rp_1", "_rp_2", "_rp_3", "_rp_4"]
        recon = 'a1_recon_miss_'
        if missionNumber == 1:
            num = str(missionNumber)
            cmd1 = "ScenEdit_SetReferencePoint({{side='{}',name='{}', lat={}, lon={}}})".format(
                side, recon + num + rp[0], aoPoints[1].latitude, aoPoints[1].longitude)
            scenario.mozi_server.send_and_recv(cmd1)
            cmd2 = "ScenEdit_SetReferencePoint({{side='{}',name='{}', lat={}, lon={}}})".format(
                side, recon + num + rp[1], rp12mid.latitude, rp12mid.longitude)
            scenario.mozi_server.send_and_recv(cmd2)
            cmd3 = "ScenEdit_SetReferencePoint({{side='{}',name='{}', lat={}, lon={}}})".format(
                side, recon + num + rp[2], rp13mid.latitude, rp13mid.longitude)
            scenario.mozi_server.send_and_recv(cmd3)
            cmd4 = "ScenEdit_SetReferencePoint({{side='{}',name='{}', lat={}, lon={}}})".format(
                side, recon + num + rp[3], rp14mid.latitude, rp14mid.longitude)
            scenario.mozi_server.send_and_recv(cmd4)
        elif missionNumber == 2:
            num = str(missionNumber)
            cmd1 = "ScenEdit_SetReferencePoint({{side='{}',name='{}', lat={}, lon={}}})".format(
                side, recon + num + rp[0], rp12mid.latitude, rp12mid.longitude)
            scenario.mozi_server.send_and_recv(cmd1)
            cmd2 = "ScenEdit_SetReferencePoint({{side='{}',name='{}', lat={}, lon={}}})".format(
                side, recon + num + rp[1], aoPoints[2].latitude, aoPoints[2].longitude)
            scenario.mozi_server.send_and_recv(cmd2)
            cmd3 = "ScenEdit_SetReferencePoint({{side='{}',name='{}', lat={}, lon={}}})".format(
                side, recon + num + rp[2], rp23mid.latitude, rp23mid.longitude)
            scenario.mozi_server.send_and_recv(cmd3)
            cmd4 = "ScenEdit_SetReferencePoint({{side='{}',name='{}', lat={}, lon={}}})".format(
                side, recon + num + rp[3], rp13mid.latitude, rp13mid.longitude)
            scenario.mozi_server.send_and_recv(cmd4)
        elif missionNumber == 3:
            num = str(missionNumber)
            cmd1 = "ScenEdit_SetReferencePoint({{side='{}',name='{}', lat={}, lon={}}})".format(
                side, recon + num + rp[0], rp13mid.latitude, rp13mid.longitude)
            scenario.mozi_server.send_and_recv(cmd1)
            cmd2 = "ScenEdit_SetReferencePoint({{side='{}',name='{}', lat={}, lon={}}})".format(
                side, recon + num + rp[1], rp23mid.latitude, rp23mid.longitude)
            scenario.mozi_server.send_and_recv(cmd2)
            cmd3 = "ScenEdit_SetReferencePoint({{side='{}',name='{}', lat={}, lon={}}})".format(
                side, recon + num + rp[2], aoPoints[3].latitude, aoPoints[3].longitude)
            scenario.mozi_server.send_and_recv(cmd3)
            cmd4 = "ScenEdit_SetReferencePoint({{side='{}',name='{}', lat={}, lon={}}})".format(
                side, recon + num + rp[3], rp34mid.latitude, rp34mid.longitude)
            scenario.mozi_server.send_and_recv(cmd4)
        else:
            num = str(missionNumber)
            cmd1 = "ScenEdit_SetReferencePoint({{side='{}',name='{}', lat={}, lon={}}})".format(
                side, recon + num + rp[0], rp14mid.latitude, rp14mid.longitude)
            scenario.mozi_server.send_and_recv(cmd1)
            cmd2 = "ScenEdit_SetReferencePoint({{side='{}',name='{}', lat={}, lon={}}})".format(
                side, recon + num + rp[1], rp13mid.latitude, rp13mid.longitude)
            scenario.mozi_server.send_and_recv(cmd2)
            cmd3 = "ScenEdit_SetReferencePoint({{side='{}',name='{}', lat={}, lon={}}})".format(
                side, recon + num + rp[2], rp34mid.latitude, rp34mid.longitude)
            scenario.mozi_server.send_and_recv(cmd3)
            cmd4 = "ScenEdit_SetReferencePoint({{side='{}',name='{}', lat={}, lon={}}})".format(
                side, recon + num + rp[3], aoPoints[4].latitude, aoPoints[4].longitude)
            scenario.mozi_server.send_and_recv(cmd4)

        # 给任务分配飞机
        mission.assign_units(totalFreeBusyInventory)


def UpdateAIAreaOfOperations(scenario):
    side = scenario.get_side_by_name('蓝方')
    defaultRef = ['AI-AO-1', 'AI-AO-2', 'AI-AO-3', 'AI-AO-4']
    defaults = {v.strName: {'latitude': v.dLatitude, 'longitude': v.dLongitude} for k, v in side.referencepnts.items()
                if v.strName in defaultRef}
    key_order = sorted(defaults.keys())
    aoPoints = [defaults[key] for key in key_order]
    coordinates = {}
    if len(aoPoints) < 4:
        hostileContacts = side.contacts
        ship_sub = side.ships.update(side.submarines)
        inventory = side.aircrafts.update(ship_sub)
        #  Loop and Get Coordinates
        for k, v in hostileContacts.items():
            coordinates[len(coordinates) + 1] = MakeLatLong(v.latitude, v.longitude)
        for k, v in inventory.items():
            coordinates[len(coordinates) + 1] = MakeLatLong(v.latitude, v.longitude)
        # Create Defense Bounding Box
        boundingBox = FindBoundingBoxForGivenLocations(coordinates, 3)
        # Create Area of Operations Zone
        for i in range(len(boundingBox)):
            cmd = "ScenEdit_SetReferencePoint({{side='{}',name='{}', lat={}, lon={}}})".format(
                side, 'AI-AO-' + str(i), boundingBox[i].latitude, boundingBox[i].longitude)
            scenario.mozi_server.send_and_recv(cmd)
            referencePoints = side.referencepnts
            referenceName = []
            for referencePoint in referencePoints.values():
                referenceName.append(referencePoint.strName)
            if ("AI-AO-" + str(i)) not in referenceName:
                side.add_reference_point("AI-AO-" + str(i), boundingBox[i].latitude, boundingBox[i].longitude)


def OffensiveConditionalCheck(scenario):
    return True


def DefensiveConditionalCheck(scenario):
    return False
