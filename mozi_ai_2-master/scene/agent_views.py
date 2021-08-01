from django.views.decorators.csrf import csrf_exempt
from django.http import QueryDict
from django.http import FileResponse
from rest_framework.decorators import api_view
from rest_framework.response import Response

from scene.models import Agent
from scene.serializers import AgentSerializerO, AgentSerializer, AgentSerializerDisplay


@csrf_exempt
@api_view(['POST'])
def add_agent(request):
    response = {}
    serializer = AgentSerializer(data=request.data)
    if serializer.is_valid():
        serializer.save()
        print(serializer.data)
        response['data'] = serializer.data
        response['message'] = 'Success'
        response['code'] = 200
    else:
        response['data'] = ''
        response['message'] = 'failed'
        response['code'] = 400
    return Response(response)


@api_view(['GET'])
def get_agent(request):
    response = {}
    try:
        agent = Agent.objects.get(id=request.GET.get('id'))
        serializer = AgentSerializerDisplay(agent)
        response['data'] = serializer.data
        response['message'] = "Success"
        response['code'] = 200
        return Response(response)
    except Agent.DoesNotExist as e:
        response['data'] = ''
        response['message'] = str(e)
        response['code'] = 404
    return Response(response)


@api_view(['GET'])
def agent_list(request):
    response = {}
    try:
        agents = Agent.objects.all()
        serializer = AgentSerializerDisplay(agents, many=True)
        response['data'] = serializer.data
        response['message'] = "Success"
        response['code'] = 200
        return Response(response)
    except Agent.DoesNotExist as e:
        response['data'] = ''
        response['message'] = str(e)
        response['code'] = 404
    return Response(response)


@api_view(['PUT'])
def update_agent(request):
    response = {}
    try:
        put = QueryDict(request.body)
        put_str = list(put.items())[0][0]   # 将获取的QueryDict对象转换为str 类型
        put_dict = eval(put_str)            # 将str类型转换为字典类型
        agent_id = put_dict.get("id")       # 获取传递参数

        agent = Agent.objects.get(id=agent_id)
        serializer = AgentSerializer(agent, data=request.data)
        if serializer.is_valid():
            serializer.save()
            response['data'] = serializer.data
            response['message'] = "Success"
            response['code'] = 200
        else:
            response['data'] = ''
            response['message'] = "Failed"
            response['code'] = 400
    except Agent.DoesNotExist as e:
        response['data'] = ''
        response['message'] = str(e)
        response['code'] = 404
    return Response(response)


@api_view(['DELETE'])
def delete_agent(request):
    response = {}
    try:
        scene = Agent.objects.get(id=request.GET.get('id'))
        scene.delete()
        response['data'] = ""
        response['message'] = "Success"
        response['code'] = 200
    except Agent.DoesNotExist as e:
        response['data'] = ''
        response['message'] = str(e)
        response['code'] = 404
    return Response(response)


@api_view(['PUT'])
def update_agent_file(request):
    response = {}
    agent_id = request.data['id']
    agent = Agent.objects.get(id=agent_id)

    code_file = request.FILES.get("code_file", None)
    if code_file:
        code_file.mode = 'rb'
        code_file_b = code_file.read()
        agent.code_file = code_file_b

    param_file = request.FILES.get("param_file", None)
    if param_file:
        param_file.mode = 'rb'
        param_file_b = param_file.read()
        agent.param_file = param_file_b

    agent.save()
    response['data'] = ''
    response['message'] = "Success"
    response['code'] = 200
    return Response(response)


@api_view(['GET'])
def download_agent(request):
    agent = Agent.objects.get(id=request.GET.get('id'))

    code_file = agent.code_file
    param_file = agent.param_file
    print(code_file)

    # file_new = open('D:/AI/1.txt', 'wb')
    # file_new.write(code_file)
    # file_new.close()

    file = open('D:/AI/2.txt', 'wb')
    file.write(code_file)
    file.close()

    file = open('D:/AI/2.txt', 'rb')
    response = FileResponse(file)
    response['Content-Type'] = 'application/octet-stream'
    response['Content-Disposition'] = 'attachment;filename="2.txt"'
    return response
