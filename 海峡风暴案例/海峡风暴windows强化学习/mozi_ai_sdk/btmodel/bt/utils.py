# 时间 ： 2020/7/29 10:23
# 作者 ： Dixit
# 文件 ： utils.py
# 项目 ： moziAI
# 版权 ： 北京华戍防务技术有限公司

from mozi_ai_sdk.btmodel.bt.basic import *
from mozi_ai_sdk.btmodel.bt.detail import *
import geopy
from geopy import distance
from math import radians, cos, sin, asin, sqrt, degrees, atan2, degrees

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
    dic = {"latitude": my_lat, "longitude": my_lon}
    return dic

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

def get_two_point_distance(lon1, lat1, lon2, lat2):
    pos1 = (lat1, lon1)
    pos2 = (lat2, lon2)
    dis = distance.vincenty(pos1, pos2)
    return dis.kilometers

def get_air_contacts(contacts):
    AirContacts = {}
    for k, v in contacts.items():
        if v.m_ContactType == 0:
            AirContacts[k] = v
    return AirContacts


def check_unit_retreat_and_compute_retreat_pos(side, unit_guid):
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
            if disKilo <= v.fAirRangeMax * 1.852:   # 海里转公里需要乘以1.852
                # 计算撤退点 TODO
                # latitude = '24.1732582268775', longitude = '155.8426299143'
                retreatPos = {'latitude': '24.1732582268775', 'longitude': '155.8426299143'}
                return True, retreatPos
        else:
            continue
    return False, None

# 根据某点(比如撤退点)计算巡逻区 TODO
def create_patrol_zone(side, pos):

    lat = pos['latitude']
    lon = pos['longitude']
    # p1 = (lat - 0.10, lon - 0.13)
    # lat: 纬度， lon：经度
    rp1 = side.add_reference_point('strike_rp1', lat + 0.3, lon - 0.3)
    rp2 = side.add_reference_point('strike_rp2', lat + 0.3, lon + 0.3)
    rp3 = side.add_reference_point('strike_rp3', lat - 0.3, lon + 0.3)
    rp4 = side.add_reference_point('strike_rp4', lat - 0.3, lon - 0.3)
    point_list = [rp1, rp2, rp3, rp4]

    return point_list

def assign_planway_to_mission(side, missionName, wayName, wayPointList, oldWayName = None):
    '''
        给任务分配(重新分配)预设航线
    :param side: 方
    :param mission:任务
    :param wayname:预设航线名称
    :param waypoint:
    航线的航路点  [{}, {}, {}, ...]
    :return:
    任务类对象
    '''

    side.add_plan_way(0, wayName)
    for point in wayPointList:
        side.add_plan_way_point(wayName, point['longitude'], point['latitude'])
    side.add_plan_way_to_mission(missionName, 1, wayName)
    if oldWayName != None:
        side.remove_plan_way(oldWayName)
    else:
        pass


# Hs_AddPlanWay('SideNameOrID',Type,'WayName')   添加预设航线
# Hs_AddPlanWayPoint('SideNameOrID','WayNameOrID',WayPointLongitude,WayPointLatitude)   为预设航线添加航路点
# Hs_UpDataPlanWayPoint('SideNameOrID','WayNameOrID','WayPointID',table)  为预设航线添加航路点
# Hs_UpDataPlanWayPoint('SideNameOrID','WayNameOrID','WayPointID',table)  修改预设航线的航路点
# Hs_RemovePlanWayPoint('SideNameOrID','WayNameOrID','WayPointID')    删除预设航线的航路点
# Hs_RemovePlanWay('SideNameOrID','WayNameOrID')   删除预设航线
# Hs_AddPlanWayToMission('MissionNameOrId',Type,'WayNameOrID')  为任务分配预设航线


def change_unit_mission(side, oldMission, newMission, units):
    '''
    改变一个或多个任务单元的任务
    :param side: 方
    :param oldmission: 旧任务
    :param newmission: 新任务
    :param units: 任务单元  [ ]
    :return:
    '''
    for unit in units:
        oldMission.unassign_unit(unit)
        newMission.assign_unit(unit)

# ScenEdit_UnAssignUnitFromMission ('AUNameOrID','MissionNameOrID')   任务中移除单元
# ScenEdit_AssignUnitToMission('AUNameOrID','MissionNameOrID')   为任务指定执行单元（方法一）
# Hs_AssignUnitListToMission('AULNameOrID','MissionNameOrID')   为任务指定执行单元（方法二）

def FindBoundingBoxForGivenContacts(side, padding = 10):
    contacts = side.contacts

    #  Variables
    defaults = [MakeLatLong(0., 0.), MakeLatLong(0., 1.), MakeLatLong(1., 1.),
                MakeLatLong(1., 0.)]
    coordinates = [btBas.MakeLatLong(defaults[0]['latitude'], defaults[0]['longitude']),
                   btBas.MakeLatLong(defaults[1]['latitude'], defaults[1]['longitude']),
                   btBas.MakeLatLong(defaults[2]['latitude'], defaults[2]['longitude']),
                   btBas.MakeLatLong(defaults[3]['latitude'], defaults[3]['longitude'])]
    contactBoundingBox = btBas.FindBoundingBoxForGivenLocations(coordinates, padding)
    contactCoordinates = []

    for k, v in contacts.items():
        contact = {}
        contact['latitude'] = v.dLatitude
        contact['longitude'] = v.dLongitude
        contactCoordinates.append(btBas.MakeLatLong(contact['latitude'], contact['longitude']))

    # Get Hostile Contact Bounding Box
    if len(contactCoordinates) > 0:
        contactBoundingBox = FindBoundingBoxForGivenLocations(contactCoordinates, padding)

    # Return Bounding Box
    return contactBoundingBox
