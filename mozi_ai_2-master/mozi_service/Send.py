# 时间 ： 2020/12/21 9:44
# 作者 ： Shizhun Xiao
# 文件 ： Sys_Send.py
# 项目 ： moziAI_nlz
# 版权 ： 北京华戍防务技术有限公司vim
from mozi_service.ScheCom import ScheCom
import json
from tools import read_config

Ip_port = read_config.ips
# 发送创建请求，返回结果vim
Zmq = ScheCom()
while True:
	sys_info=Zmq.Send_Req("sys_info",Ip_port[1])# 发送获取系统信息请求 sys_info
	sys_dict=json.loads(sys_info)
	print("sys_info:", sys_dict)

	# docker_info=Zmq.Send_Req("docker_info",Ip_port[1])#发送获取docker进程信息的请求
	# docker_dict=json.loads(docker_info)
	# print("docker_info:",docker_dict)
	#
	# ray_info=Zmq.Send_Req("ray_info",Ip_port[1])#发送获取ray进程信息的请求
	# ray_dict=json.loads(ray_info)
	# print("ray_info:",ray_dict)
