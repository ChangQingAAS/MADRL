import numpy as np

from mozi_ai_sdk.env import base_env

import etc
import log_utils
from geo_utils import get_point_with_point_bearing_distance
from geo_utils import get_degree
from geo_utils import get_two_point_distance


class Env_Uav_Avoid_Tank(base_env.BaseEnvironment):
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
        # 状态空间维度: 经度，维度，朝向.这里想定文件里是4个无人机，所以4 * 3 = 12
        # 关于这个参数能不能优化成： agents_num * 3，暂时搁置
        self.state_space_dim = 12
        # 改变朝向
        self.action_space_dim = 1
        self.action_max = 1

        self.red_unit_list = None
        self.observation = None
        self.red_side_name = "无人机群"
        self.blue_side_name = "障碍物"

    def reset(self):
        """
        重置
        返回：当前状态及回报值
        """
        # 调用父类的重置函数
        super(Env_Uav_Avoid_Tank, self).reset(etc.app_mode)

        # 构建各方实体
        self._construct_side_entity()
        self._init_unit_list()

        state_now = self.get_observation()
        reward_now = self.get_reward(None)
        return state_now, reward_now

    def execute_action(self, action_value):
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
        super(Env_Uav_Avoid_Tank, self).step()

        # 根据动作计算飞机的期望路径点
        waypoint = self._get_aircraft_waypoint(action_value)
        
        # 当前的位置
        # longitude = self.observation[0]
        # latitude = self.observation[1]

        # 无人机群
        airs = self.redside.aircrafts
        # for debug
        # print("airs is", airs)
        for guid in airs:
            # for debug
            # print("guid is ", guid)
            aircraft = airs[guid]
            lon = float(waypoint["longitude"])
            lat = float(waypoint["latitude"])
            # print("set waypoint:%s %s" % (lon, lat))
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
        # # after check_done()
        print("done is ", done)

        return np.array(obs), reward

    def check_done(self, action_value):
        """
        检查是否可以结束：
            ①到达目标地点附近则结束
            ②超出目标地点太远则结束
        """
        waypoint = self._get_aircraft_waypoint(action_value)
        lon = float(waypoint["longitude"])
        lat = float(waypoint["latitude"])
        target_lon, target_lat = self.get_target_point()

        lat_flag = (lat <
                    (float(target_lat) + 0.1)) and (lat >
                                                    (float(target_lat) - 0.1))
        lon_flag = (lon <
                    (float(target_lon) + 0.1)) and (lon >
                                                    (float(target_lon) - 0.1))

        exit_flag = (abs(float(target_lat) - lat) >
                     0.5) or (abs(float(target_lon) - lon) > 0.5)

        # 到达目标地点附近
        if lon_flag and lat_flag:
            print("UAVs are in traget area now!")
            print("current_lon is ", lon)
            print("current_lat is ", lat)
            print("\n")

            return True

        # 超出目标地点太远
        if exit_flag:
            print("UAV are too far beyond the target area!")
            print("current_lon is ", lon)
            print("current_lat is ", lat)
            print("\n")

            return True

        return False

    def get_reward(self, action_value):
        reward = 0.0
        if action_value != None:
            # 距离目标越近，奖励值越大
            distance_reward = self.get_distance_reward(action_value)
            reward += distance_reward
        return reward

    def get_distance_reward(self, action_value):
        """
        获取距离奖励
        """
        obs = self.observation

        # 这里用了一个Agent1代表多智能体群的位置
        current_lon = obs[0]
        current_lat = obs[1]
        current_heading = obs[2]

        # 朝向角改变幅度，这里有一个超参
        action_heading_change = action_value * 5

        # 获取到目标点的距离和角度
        target_lat, target_lon = self.get_target_point()
        distance = self.get_target_distance(current_lat, current_lon)
        task_heading = get_degree(current_lat, current_lon, target_lat,
                                  target_lon)

        # 改变朝向角
        current_heading += action_heading_change

        reward = self.get_reward_value(current_lat, current_lon, task_heading,
                                       current_heading, distance)

        return reward

    def get_reward_value(self, lat, lon, task_heading, current_heading,
                         distance):
        """
        由于不好确定agent和目标的距离，在这里使用的reward没有涉及到每次移动距离R
        """
        # todo:
        #   后续还要考虑怎么把自己agent的奖惩拆开
        #   现在好像是在一起的样子

        aide_reward = 0
        main_reward = -abs(distance) / 3000.0

        # 拿到障碍方的列表
        unit_list = []
        facilities_list_dic = self.blueside.facilities
        for key in facilities_list_dic:
            unit_list.append(key)

        # 循环每个障碍体，求和辅助reward
        for key in unit_list:
            facilities_list_dic = self.blueside.facilities
            unit = facilities_list_dic.get(key)
            # for debug
            # print("\nunit is", unit)
            # print("\nunit.dLongitude is ", unit.dLongitude)
            if unit:
                obstacle_lon = unit.dLongitude
                obstacle_lat = unit.dLatitude
                distance = get_two_point_distance(lon, lat, obstacle_lon,
                                                  obstacle_lat)
                aide_reward += abs(distance) / 1000.0
                # 添加 十分靠近障碍物的惩罚
                if (obstacle_lon - 0.05 <= lon <= obstacle_lon + 0.05) and (
                        obstacle_lat - 0.05 <= lat <= obstacle_lat + 0.05):
                    print("aircraft is too close to obs!")
                    aide_reward -= 100

        print("辅助reward is ", aide_reward)
        print("主线reward is ", main_reward)

        reward = main_reward + aide_reward
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
        这里的distance是每次飞机前进的长度，应该和速度是一样的，也算是一个超参吧
        """
        dic = get_point_with_point_bearing_distance(lat, lon, heading,
                                                    distance)
        return dic

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
        print(" action is ", action_value)
        waypoint_heading = self._get_waypoint_heading(heading,
                                                      action_value * 5)
        waypoint = self._get_new_waypoint(waypoint_heading, latitude,
                                          longitude)

        return waypoint

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
        # 初始化单元列表
        self.red_unit_list = self._init_red_unit_list()

    def get_target_point(self):
        """
        获取目标点
        """
        target_lat = etc.task_end_point["latitude"]
        target_lon = etc.task_end_point["longitude"]
        return target_lat, target_lon

    def get_target_distance(self, lat, lon):
        """
        获取目标距离
        """
        target_lat, target_lon = self.get_target_point()
        distance = get_two_point_distance(lon, lat, target_lon, target_lat)
        return distance
