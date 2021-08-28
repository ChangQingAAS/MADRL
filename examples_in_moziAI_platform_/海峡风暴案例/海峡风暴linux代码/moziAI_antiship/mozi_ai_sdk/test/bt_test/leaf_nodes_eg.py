# by aie


import re
from mozi_ai_sdk.btmodel.bt import utils
from mozi_simu_sdk.geo import get_horizontal_distance, get_end_point
from mozi_simu_sdk.mssnpatrol import CPatrolMission
from mozi_simu_sdk.mssnstrike import CStrikeMission

lst = ['闪电 #5', '闪电 #6', '闪电 #7', '闪电 #8', '闪电 #9', '闪电 #10', '闪电 #11', '闪电 #12', '闪电 #13', '闪电 #14', '闪电 #15',
       '闪电 #16']


# 选择不同任务的条件判断,如果蓝方飞机剩余小于6架，就启动反舰任务
def antiship_condition_check(scenario):
    """
    by dixit
    :param scenario:
    :return:

    """
    side = scenario.get_side_by_name('蓝方')
    side.static_update()
    airs = side.aircrafts
    if len(airs) <= 14:
        return True
    else:
        return False


# 创建反舰任务
def create_antisurfaceship_mission(scenario):
    side = scenario.get_side_by_name('红方')
    contacts = side.contacts
    ss = side.ships
    airs_dic = side.aircrafts
    # 获取反舰任务飞机
    airs_1 = {k: v for k, v in airs_dic.items() if int(re.sub('\D', '', v.strName)) < 3}
    airs_2 = {k: v for k, v in airs_dic.items() if 2 <= int(re.sub('\D', '', v.strName)) <= 2}
    if len(contacts) == 0 or len(airs_1) + len(airs_2) == 0:
        return False
    # 等巡逻的飞机全部起飞后，打击任务创建，然后开始起飞
    airs_patrol = side.patrolmssns
    if airs_patrol is False:
        return False

    targets = {k: v for k, v in contacts.items() if (('DDG' in v.strName) | ('CVN' in v.strName))}
    # 验证是否会打己方舰艇
    target_2 = {k: v for k, v in ss.items() if ('DDG' in v.strName)}
    target_1 = {k: v for k, v in contacts.items() if ('DDG' in v.strName)}
    mssnSitu = side.strikemssns
    if {k: v for k, v in mssnSitu.items() if v.strName == 'strike1'}.__len__() == 0:
        side.add_mission_strike('strike1', 2)
        strkmssn_1 = CStrikeMission('T+1_mode', scenario.mozi_server, scenario.situation)
        strkmssn_1.strName = 'strike1'
        # 取消满足编队规模才能起飞的限制（任务条令）
        strkmssn_1.set_flight_size_check('红方', 'strike1', 'false')
    else:
        return False
    strkmssn_1.assign_targets(target_1)
    strkmssn_1.assign_units(airs_1)
    if {k: v for k, v in mssnSitu.items() if v.strName == 'strike2'}.__len__() == 0:
        side.add_mission_strike('strike2', 2)
        strkmssn_2 = CStrikeMission('T+1_mode', scenario.mozi_server, scenario.situation)
        strkmssn_2.strName = 'strike2'
        # 取消满足编队规模才能起飞的限制（任务条令）
        strkmssn_2.set_flight_size_check('红方', 'strike2', 'false')
    else:
        return False
    strkmssn_2.assign_targets(target_2)
    strkmssn_2.assign_units(airs_2)

    # 通过 ctrl +x 拿到航线设置的点
    wayPointList1 = [{'latitude': '26.0979297169117', 'longitude': '153.365146994643'},
                     {'latitude': '26.3202842588887', 'longitude': '156.042461903776'},]
    utils.assign_planway_to_mission(side, 'strike1', 'strike1Way', wayPointList1)

    wayPointList2 = [{'latitude': '25.2543871879078', 'longitude': '153.238096612711'},
                     {'latitude': '25.0437456203838', 'longitude': '156.012005422884'},]
    utils.assign_planway_to_mission(side, 'strike2', 'strike2Way', wayPointList2)
    return False


def update_antisurfaceship_mission(scenario):
    side = scenario.get_side_by_name('红方')
    side1 = scenario.get_side_by_name('蓝方')
    airs_dic = side.aircrafts
    airsOnMssn = {k: v for k, v in airs_dic.items() if v.strActiveUnitStatus.find('正在执行任务') > 0}
    airs = {k: v for k, v in airs_dic.items() if int(re.sub('\D', '', v.strName)) < 9}
    contacts = side.contacts
    if airsOnMssn.__len__() == 0:
        return False
    if len(contacts) == 0 or len(airs) == 0:
        return False

    mssnSitu = side.strikemssns
    strkmssn = [v for v in mssnSitu.values() if 'strike' in v.strName]
    if len(strkmssn) != 2:
        return False
    strkmssn_1 = [v for v in mssnSitu.values() if v.strName == 'strike1'][0]

    strkmssn_2 = [v for v in mssnSitu.values() if v.strName == 'strike2'][0]
    # 设置任务条令
    doctrine = strkmssn_1.get_doctrine()
    # doctrine.set_emcon_according_to_superiors('false')
    # 3：是, 编组成员达到武器状态时离开编队返回基地
    if doctrine.m_WeaponStateRTB != 3:
        doctrine.set_weapon_state_for_air_group('3')  # m_WeaponStateRTB
    if doctrine.m_GunStrafeGroundTargets != 1:
        doctrine.gun_strafe_for_aircraft('1')  # m_GunStrafeGroundTargets
        # 0：自杀式攻击，不返回基地
    if doctrine.m_BingoJokerRTB != 0:
        doctrine.set_fuel_state_for_air_group('0')  # m_BingoJokerRTB
        # 0， 对潜目标自由开火
    if doctrine.m_WCS_Submarine != 0:
        doctrine.set_weapon_control_status('weapon_control_status_subsurface', '0')
        # 0， 对海目标自由开火
    if doctrine.m_WCS_Surface != 0:
        doctrine.set_weapon_control_status('weapon_control_status_surface', '0')
        # 0， 对地目标自由开火
    if doctrine.m_WCS_Land != 0:
        doctrine.set_weapon_control_status('weapon_control_status_land', '0')
        # 0， 对空目标自由开火
    if doctrine.m_WCS_Air != 0:
        doctrine.set_weapon_control_status('weapon_control_status_air', '0')

    doctrine_2 = strkmssn_2.get_doctrine()
    # doctrine.set_emcon_according_to_superiors('false')
    if doctrine_2.m_WeaponStateRTB != 3:
        doctrine_2.set_weapon_state_for_air_group('3')  # m_WeaponStateRTB
    if doctrine_2.m_GunStrafeGroundTargets != 1:
        doctrine_2.gun_strafe_for_aircraft('1')  # m_GunStrafeGroundTargets
    if doctrine_2.m_BingoJokerRTB != 0:
        doctrine_2.set_fuel_state_for_air_group('0')  # m_BingoJokerRTB
    if doctrine_2.m_WCS_Submarine != 0:
        doctrine_2.set_weapon_control_status('weapon_control_status_subsurface', '0')
    if doctrine_2.m_WCS_Surface != 0:
        doctrine_2.set_weapon_control_status('weapon_control_status_surface', '0')
    if doctrine_2.m_WCS_Land != 0:
        doctrine_2.set_weapon_control_status('weapon_control_status_land', '0')
    if doctrine_2.m_WCS_Air != 0:
        doctrine_2.set_weapon_control_status('weapon_control_status_air', '0')

    mssnSitu = side.strikemssns
    patrolmssn = side.patrolmssns
    target = {k: v for k, v in contacts.items() if ('DDG' in v.strName)}

    strkmssn = [v for v in mssnSitu.values() if v.strName == 'strike2'][0]
    strkPatrol = [v for v in patrolmssn.values() if v.strName == 'strikePatrol']

    # 获取任务执行单元
    missionUnits = strkmssn.m_AssignedUnits.split('@')
    create = False
    # for unitGuid in missionUnits:
    #     retreat, retreatPos = utils.check_unit_retreat_and_compute_retreat_pos(side, unitGuid)
    #     if retreat:
    #         if len(strkPatrol) == 0 & create is False:
    #             pos = {'latitude': list(target.values())[0].dLatitude, 'longitude': list(target.values())[0].dLongitude}
    #             point_list = utils.create_patrol_zone(side, pos)
    #             postr = []
    #             for point in point_list:
    #                 postr.append(point.strName)
    #             side.add_mission_patrol('strikePatrol', 1, postr)
    #             strikePatrolmssn = CPatrolMission('T+1_mode', scenario.mozi_server, scenario.situation)
    #             strikePatrolmssn.strName = 'strikePatrol'
    #             # 取消满足编队规模才能起飞的限制（任务条令）
    #             strikePatrolmssn.set_flight_size_check('false')
    #             utils.change_unit_mission(side, strkmssn, strikePatrolmssn, missionUnits)
    #             return False
    #         else:
    #             break
    return False


# 更新巡逻任务,主要功能是两艘轮船往中间经纬度开动
def update_patrol_mission(scenario):
    side = scenario.get_side_by_name('红方')
    # 从敌方所有单元中取到目标
    targets = side.contacts
    target = [v for k, v in targets.items() if '阿里伯克' in v.strName]
    geopoint_target = None
    if target:
        geopoint_target = (target[0].dLatitude, target[0].dLongitude)

    # 巡逻任务1,2飞机飞行的路线设置的航路点
    xl1_lat = 0
    xl2_lat = 0
    for point in side.referencepnts.values():
        if point.strName == 'rp2':
            xl1_lat = point.dLatitude
        elif point.strName == 'rp6':
            xl2_lat = point.dLatitude
    airs_dic = side.aircrafts

    # 执行任务的飞机,
    airs = {k: v for k, v in airs_dic.items() if int(re.sub('\D', '', v.strName)) >= 5}


    # 获取巡逻任务，如果巡逻任务为0，说明还没有，创建巡逻任务。
    patrol_missions_dic = side.get_patrol_missions()
    patrol_missions = [mission for mission in patrol_missions_dic.values()]
    if len(patrol_missions) == 0:
        return False

    # 如果有任务，就每个任务更新，包含给任务分配飞机，1/3规则
    for patrol_mission in patrol_missions:
        if patrol_mission.strName == 'xl1':
            doctrine_xl1 = patrol_mission.get_doctrine()
            airs_xl1 = {k: airs[k] for k, v in airs.items() if v.strName in lst[:3]}
            patrol_mission.assign_units(airs_xl1)
            patrol_mission.set_flight_size(1)


        if patrol_mission.strName == 'xl3':
            airs_xl3 = {k: airs[k] for k, v in airs.items() if v.strName in lst[6:8]}
            patrol_mission.assign_units(airs_xl3)

        if patrol_mission.strName == 'xl4':
            doctrine_xl4 = patrol_mission.get_doctrine()
            airs_xl4 = {k: airs[k] for k, v in airs.items() if v.strName in lst[8:]}
            patrol_mission.assign_units(airs_xl4)
            patrol_mission.set_flight_size(1)

            for air in airs_xl4.values():
                evade_ship(geopoint_target, air, doctrine_xl4)
    update_patrol_zone(scenario)
    return False


# 躲避驱逐舰接口
def evade_ship(geopoint_target, air, mission_doctrine):
    geopoint_air = (air.dLatitude, air.dLongitude)
    if geopoint_target:
        dis = get_horizontal_distance(geopoint_air, geopoint_target)
        if dis <= 60:
            mission_doctrine.ignore_plotted_course('yes')
            genpoint_away = get_end_point(geopoint_air, 15, (air.fCurrentHeading + 150))
            air.plot_course([genpoint_away])


# 创建巡逻任务
def create_patrol_mission(scenario):
    side = scenario.get_side_by_name('红方')
    airs_dic = side.aircrafts
    patrol_missions_dic = side.get_patrol_missions()
    if len(patrol_missions_dic) == 4:
        return False
    airs_c = [v for v in airs_dic.values() if 4 < int(re.sub('\D', '', v.strName)) < 9]  # 编号5，6,7,8的,4架飞机
    for air in airs_c:
        # 如果此4架飞机的挂载还是原来的挂载，那么修改挂载id 为 19364
        if 'AGM' in air.m_UnitWeapons:
            air.set_loudout('19364', 1)
    # patrol_missions_dic = side.get_patrol_missions()
    patrol_mission_name = [mission.strName for mission in patrol_missions_dic.values()]
    # 根据驱逐舰的坐标，确定巡逻区参考点，根据巡逻区参考点，创建巡逻区
    point_list = create_patrol_zone(scenario)
    i = 1
    for point in point_list:
        point_str = []
        for name in point:
            point_str.append(name.strName)
        # 新建巡逻区名字
        patrol_name = 'xl' + str(i)
        # 更新巡逻任务,给巡逻任务添加移动后的参考位点。
        if patrol_name in patrol_mission_name:
            for patrol in patrol_missions_dic.values():
                if patrol_name == patrol.strName:
                    patrol.add_patrol_zone('红方', patrol_name, point_str)
        else:
            # 创建巡逻任务，设置1/3规则
            side.add_mission_patrol(patrol_name, 0, point_str)
            patrolmssn = CPatrolMission('T+1_mode', scenario.mozi_server, scenario.situation)
            patrolmssn.strName = patrol_name
            patrolmssn.set_one_third_rule('红方', 'true')
        i += 1
    return False


# 巡逻区域经纬度的生成
def create_patrol_zone(scenario):
    side = scenario.get_side_by_name('红方')
    ships = side.ships
    point_list = []
    # 根据本方航空母舰的位置创建巡逻区xl1，xl2
    for k, v in ships.items():
        # lat: 纬度， lon：经度
        if '驱逐舰' in v.strName:
            lat, lon = v.dLatitude, v.dLongitude
            # xl1
            rp1 = side.add_reference_point('rp1', lat + 1.2, lon + 1)
            rp2 = side.add_reference_point('rp2', lat + 1, lon + 1.5)
            rp3 = side.add_reference_point('rp3', lat + 0.6, lon + 1)
            rp4 = side.add_reference_point('rp4', lat + 1, lon + 0.5)
            point_list.append([rp1, rp2, rp3, rp4])
            # xl2
            rp5 = side.add_reference_point('rp5', lat - 0.7, lon + 1)
            rp6 = side.add_reference_point('rp6', lat - 1, lon + 1.5)
            rp7 = side.add_reference_point('rp7', lat - 1.2, lon + 1)
            rp8 = side.add_reference_point('rp8', lat - 1, lon + 0.6)
            point_list.append([rp5, rp6, rp7, rp8])
            # xl3
            rp13 = side.add_reference_point('rp13', lat + 0.25, lon - 1)
            rp14 = side.add_reference_point('rp14', lat + 0.25, lon - 0.3)
            rp15 = side.add_reference_point('rp15', lat - 0.25, lon - 0.3)
            rp16 = side.add_reference_point('rp16', lat - 0.25, lon - 1)
            point_list.append([rp13, rp14, rp15, rp16])
    contacts = side.contacts
    # 根据对方驱逐舰位置创建巡逻区 xl4
    for contact in contacts.values():
        if '驱逐舰' in contact.strName:
            lat1, lon1 = contact.dLatitude, contact.dLongitude
            rp9 = side.add_reference_point('rp9', lat1 + 0.7, lon1 - 0.5)
            rp10 = side.add_reference_point('rp10', lat1 + 0.7, lon1 + 0.5)
            rp11 = side.add_reference_point('rp11', lat1 - 0.7, lon1 + 0.5)
            rp12 = side.add_reference_point('rp12', lat1 - 0.7, lon1 - 0.5)
            point_list.append([rp9, rp10, rp11, rp12])
            # point_list = [[rp1, rp2, rp3, rp4],[rp5, rp6, rp7, rp8],[rp9, rp10, rp11, rp12]]
    return point_list


# 更新巡逻区
def update_patrol_zone(scenario):
    side = scenario.get_side_by_name('红方')
    ships = side.ships
    # 根据本方航空母舰的位置创建巡逻区xl1，xl2
    for k, v in ships.items():
        # lat: 纬度， lon：经度
        if '驱逐舰' in v.strName:
            lat, lon = v.dLatitude, v.dLongitude
            # xl1
            side.set_reference_point('rp1', lat + 1.2, lon + 1)
            side.set_reference_point('rp2', lat + 1, lon + 1.5)
            side.set_reference_point('rp3', lat + 0.6, lon + 1)
            side.set_reference_point('rp4', lat + 1, lon + 0.5)
            # xl2
            side.set_reference_point('rp5', lat - 0.7, lon + 1)
            side.set_reference_point('rp6', lat - 1, lon + 1.5)
            side.set_reference_point('rp7', lat - 1.2, lon + 1)
            side.set_reference_point('rp8', lat - 1, lon + 0.6)

            # xl3
            side.set_reference_point('rp13', lat + 0.25, lon - 1)
            side.set_reference_point('rp14', lat + 0.25, lon - 0.3)
            side.set_reference_point('rp15', lat - 0.25, lon - 0.3)
            side.set_reference_point('rp16', lat - 0.25, lon - 1)

    contacts = side.contacts
    # 根据对方驱逐舰位置创建巡逻区 xl4
    for contact in contacts.values():
        if '驱逐舰' in contact.strName:
            lat1, lon1 = contact.dLatitude, contact.dLongitude
            side.set_reference_point('rp9', lat1 + 0.7, lon1 - 0.5)
            side.set_reference_point('rp10', lat1 + 0.7, lon1 + 0.5)
            side.set_reference_point('rp11', lat1 - 0.7, lon1 + 0.5)
            side.set_reference_point('rp12', lat1 - 0.7, lon1 - 0.5)
