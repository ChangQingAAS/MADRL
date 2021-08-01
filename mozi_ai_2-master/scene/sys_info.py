from rest_framework.decorators import api_view
from rest_framework.response import Response
from mozi_service.ScheCom import ScheCom
from tools import read_config


@api_view(['GET'])
def get_sys_info_all(request):
    response = {}

    ip_ports = read_config.ips
    # 发送创建请求，返回结果vim
    zmq = ScheCom()
    sys_info_all = []
    for ip_port in ip_ports:
        sys_info = {'server_ip': ip_port.split(':')[0]}
        sys_info.update(eval(zmq.Send_Req("sys_info", ip_port)))
        sys_info_all.append(sys_info)

    response['data'] = sys_info_all
    response['message'] = "Success"
    response['code'] = 200
    return Response(response)
