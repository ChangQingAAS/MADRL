import datetime
import random
import numpy as np
from math import cos
from math import radians
from mozi_utils import pylog
from mozi_utils.geo import get_point_with_point_bearing_distance
from mozi_utils.geo import get_degree
from mozi_utils.geo import get_two_point_distance

from mozi_ai_sdk.env import base_env
import etc_uav_anti_tank
'''
功能：无人机反坦克想定环境类，UAT=UAV Anti Tank
'''


class EnvUavAntiTank(base_env.BaseEnvironment):
    """
    功能：构造函数
    """
    def __init__(self,
                 IP,
                 AIPort,
                 scenario_name,
                 simulate_compression,
                 duration_interval,
                 server_plat="windows"):
        super().__init__(IP, AIPort, server_plat, scenario_name,
                         simulate_compression, duration_interval)

        self.SERVER_PLAT = server_plat
        self.state_space_dim = 12  # 状态空间维度: 经度，维度，朝向
        self.action_space_dim = 1  # 改变朝向
        self.action_max = 1

        self.red_unit_list = None
        self.observation = None
        self.red_side_name = "红方"
        self.blue_side_name = "蓝方"

    def reset(self):
        """
        重置
        返回：当前状体及回报值
        """
        # 调用父类的重置函数
        super(EnvUavAntiTank, self).reset(etc_uav_anti_tank.app_mode)

        # 构建各方实体
        self._construct_side_entity()
        self._init_unit_list()

        state_now = self.get_observation()
        reward_now = self.get_reward(None)
        return state_now, reward_now

    '''
    功能：环境的执行动作函数
    流程：
        输入动作
        执行动作
        更新态势
        获取观察
        获取reward
        检查是否结束
    返回： 1）state：状态；
           2）reward：回报值
    '''

    def execute_action(self, action_value):
        super(EnvUavAntiTank, self).step()

        # 根据动作计算飞机的期望路径点
        waypoint = self._get_aircraft_waypoint(action_value)
        # 当前的位置
        # longitude = self.observation[0]
        # latitude = self.observation[1]

        # 红方的飞机
        airs = self.redside.aircrafts
        # for debug
        # print("airs is", airs)
        for guid in airs:
            # for debug
            # print("guid is ", guid)
            aircraft = airs[guid]
            # todo 改成设计的奖励函数
            lon, lat = self._deal_point_data(waypoint)
            #print("set waypoint:%s %s" % (lon, lat))
            aircraft.set_waypoint(lon, lat)

        # 动作下达了，该仿真程序运行，以便执行指令
        self.mozi_server.run_grpc_simulate()

        # 更新数据时，会被阻塞，实现与仿真的同步
        self._update()

        # # 动作执行完了，该继续仿真了
        # self.mozi_server.run_simulate()

        obs = self.get_observation()
        reward = self.get_reward(action_value)
        done = self.check_done(action_value)
        # for debug
        # print("obs is ", obs)
        # print("reward is ", reward)
        print("[after check_done()] done is ", done)

        return np.array(obs), reward

    def check_done(self,action_value):
        """
        检查是否可以结束
        如果到达目标地点附近则结束
        """
        waypoint = self._get_aircraft_waypoint(action_value)
        lon, lat = self._deal_point_data(waypoint)
        target_lon, target_lat = self.get_target_point()
        lat_flag = (lat < (float(target_lat) + 0.1)) and (lat > (float(target_lat) - 0.1))
        lon_flag = (lon < (float(target_lon) + 0.1)) and (lon > (float(target_lon) - 0.1))

        exit_flag = (abs(float(target_lat) - lat) > 0.5) or (abs(float(target_lon) - lon) > 0.5)

        if lon_flag and lat_flag:
            print("UAVs are in traget area now !")
            print("\n",lon,lat)
            return True

        if exit_flag:
            print("UAV are out of possible target area! ")
            return True

        return False

    def get_reward(self, action_value):
        """
        获取奖励
        """
        reward = 0.0
        # todo 更改奖励函数
        if action_value != None:
            # 距离目标越近，奖励值越大
            distance_reward, distance = self._get_distance_reward(action_value)
            reward += distance_reward
        return reward

    def _get_distance_reward(self, action_value):
        """
        获取距离奖励
        """
        obs = self.observation
        longitude = obs[0]
        latitude = obs[1]
        heading = obs[2]

        distance = self.get_target_distance(latitude, longitude)
        # 朝向角改变幅度，这里有一个超参
        action_change_heading = action_value[0].item() * 5
        reward = self.get_distance_reward(latitude, longitude, heading,
                                          action_change_heading)
        return reward, distance

    def get_distance_reward(self, lat, lon, last_heading, heading_change):
        """
        获取距离奖励值
        """
        target_lat, target_lon = self.get_target_point()
        distance = get_two_point_distance(lon, lat, target_lon, target_lat)
        task_heading = get_degree(lat, lon, target_lat, target_lon)
        current_heading = last_heading + heading_change
        return self.get_reward_value(task_heading, current_heading,
                                     distance)

    def get_reward_value(self, task_heading, current_heading, distance):
        """
        由于不好确定agent和目标的距离，在这里使用的reward没有涉及到每次移动距离R
        todo: 辅助reward
            question: 怎么找到障碍物的位置
        """
        reward = - abs(distance) / 10000.0
        return reward

    def _init_red_unit_list(self):
        """
        初始化红方单元列表
        """
        ret_lt = []
        aircraft_list_dic = self.redside.aircrafts
        for key in aircraft_list_dic:
            ret_lt.append(key)
        return ret_lt

    def _get_a_side_observation(self, unit_list):
        """
        获取一方的观察
        """
        obs_lt = [0.0 for x in range(0, self.state_space_dim)]
        count = 0
        for key in unit_list:
            aircraft_list_dic = self.redside.aircrafts
            # for debug
            # print("aircraft_list_dic is", aircraft_list_dic)
            unit = aircraft_list_dic.get(key)
            # for debug
            # print("\nunit is", unit)
            print("")
            if unit:
                obs_lt[count * 3 + 0] = unit.dLongitude
                obs_lt[count * 3 + 1] = unit.dLatitude
                obs_lt[count * 3 + 2] = unit.fCurrentHeading
                count += 1
        return obs_lt

    def _get_red_observation(self):
        """
        获取红方的观察
        """
        unit_list = self.red_unit_list
        obs_lt = self._get_a_side_observation(unit_list)
        return obs_lt

    def _get_waypoint_heading(self, last_heading, action_value):
        """
        获取航路点朝向
        """
        current_heading = last_heading + action_value
        if current_heading < 0:
            current_heading += 360
        if current_heading > 360:
            current_heading -= 360
        return current_heading

    def _get_new_waypoint(self, heading, lat, lon, distance=20.0):
        """
        根据朝向，设置飞机的下一个路径点
        """
        dic = get_point_with_point_bearing_distance(lat, lon, heading,
                                                    distance)
        return dic

    def _deal_point_data(self, waypoint):
        """
        处理航路点数据：把waypoint 字典里的参数转成str类型
        不知道为什么要转类型，应该按浮点数算更好吧
        """
        lon = float(waypoint["longitude"])
        lat = float(waypoint["latitude"])
        return lon, lat

    def _get_aircraft_waypoint(self, action_value):
        """
        根据智能体的动作指令，获取飞机的期望的航路点
        """
        obs = self.observation
        # 当前的位置
        longitude = obs[0]
        latitude = obs[1]
        # 朝向
        heading = obs[2]
        # 航路点朝向角改变幅度，这里有一个超参，现设置为5
        waypoint_heading = self._get_waypoint_heading(
            heading, action_value[0].item() * 5)
        waypoint = self._get_new_waypoint(waypoint_heading, latitude,
                                          longitude)

        return waypoint

    # def _check_aircraft_exist(self):
    #     obs = self.observation
    #     for i in range(len(obs)):
    #         if obs[i] != 0.0:
    #             return True
    #     return False

    # # for question
    # # 这里是不是有逻辑错误（无，CFacility是按一个整体算的
    # def _check_target_exist(self):
    #     ret = self.scenario.get_units_by_name(etc_uav_anti_tank.target_name)
    #     # for debug
    #     print("目标的名字： ", ret)
    #     for key in ret:
    #         ret = self.scenario.unit_is_alive(key)
    #         # for debug
    #         print("ret is", ret)
    #         if not ret:
    #             #pylog.info("target is not exist")
    #             # for debug
    #             print("target is not exist")
    #             pass
    #         else:
    #             #pylog.info("target is exist")
    #             # for debug
    #             print("target is exist")
    #             pass
    #         return ret
    #     return False

    def _get_target_guid(self):
        """
        获取目标guid
        """
        target_name = etc_uav_anti_tank.target_name
        # for debug
        print("target_name is ", target_name)
        print("blueside.facilities is ", blueside.facilities)
        for key in self.blueside.facilities:
            pylog.info("%s" % self.blueside.facilities[key])
            if etc_uav_anti_tank.target_name == self.blueside.facilities[
                    key].strName:
                target_guid = key
                return target_guid
        return target_guid

    def _get_contact_target_guid(self):
        target_name = etc_uav_anti_tank.target_name
        if self.redside.contacts:
            for key in self.redside.contacts:
                pylog.info("contact guid:%s" % key)
                dic = self.redside.contacts[key].__dict__
                actual_guid = self.redside.contacts[key].m_ActualUnit
                if etc_uav_anti_tank.target_name == self.blueside.facilities[
                        actual_guid].strName:
                    return key

                #pylog.info("contact actual guid:%s" % actual_guid)
                #for k in self.blueside.facilities:
                #   if etc_uav_anti_tank.target_name == self.blueside.facilities[k].strName:
                #       return key

    def _check_is_contact_target(self):
        target_name = etc_uav_anti_tank.target_name
        if self.redside.contacts:
            for key in self.redside.contacts:
                dic = self.redside.contacts[key].__dict__
                actual_guid = self.redside.contacts[key].m_ActualUnit
                for k in self.blueside.facilities:
                    if etc_uav_anti_tank.target_name == self.blueside.facilities[
                            k].strName:
                        target_guid = k
                        return target_guid
        return False

    def _check_is_find_target(self):
        """
        检查是否发现目标
        """
        target_name = etc_uav_anti_tank.target_name
        target_guid = self._check_is_contact_target()
        if target_guid:
            pylog.info("find target and the name is:%s, the guid is:%s" %
                       (target_name, target_guid))
            return True

        return False

    def _update(self):
        self.mozi_server.update_situation(self.scenario)
        self.redside.static_update()
        self.blueside.static_update()

    def get_observation(self):
        """
        获取观察
        """
        red_obs_lt = self._get_red_observation()
        self.observation = red_obs_lt
        return red_obs_lt

    def _construct_side_entity(self):
        """
        构造各方实体
        """
        self.redside = self.scenario.get_side_by_name(self.red_side_name)
        self.redside.static_construct()
        self.blueside = self.scenario.get_side_by_name(self.blue_side_name)
        self.blueside.static_construct()

    def _init_unit_list(self):
        """
        初始化单元列表
        """
        self.red_unit_list = self._init_red_unit_list()

    def get_target_point(self):
        """
        获取目标点
        """
        lat2 = etc_uav_anti_tank.task_end_point["latitude"]
        lon2 = etc_uav_anti_tank.task_end_point["longitude"]
        return lat2, lon2

    def get_target_distance(self, lat, lon):
        """
        获取目标距离
        """
        lat2, lon2 = self.get_target_point()
        distance = get_two_point_distance(lon, lat, lon2, lat2)
        return distance