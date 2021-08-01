from django.views.decorators.csrf import csrf_exempt
from django.http import FileResponse
from django.http import QueryDict
from rest_framework import generics
from rest_framework.decorators import api_view
from rest_framework.response import Response
import threading
import time

from scene.models import Scene, Agent
from scene.serializers import SceneSerializer, SceneSerializerO, ScenarioSerializer, SceneSerializerDisplay, AgentSerializer
import mozi_service.stubs as stubs


class AddScenario(generics.CreateAPIView):
    queryset = Scene.objects.all()
    serializer_class = ScenarioSerializer


class UpdateAgent(generics.UpdateAPIView):
    queryset = Agent.objects.all()
    serializer_class = AgentSerializer


@csrf_exempt
@api_view(['POST'])
def add_scene(request):
    response = {}
    print(request.data)
    serializer = SceneSerializer(data=request.data)
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
def show_scenes(request):
    response = {}
    try:
        scenes = Scene.objects.filter()
        serializer = SceneSerializerDisplay(scenes, many=True)
        response['data'] = serializer.data
        response['message'] = "Success"
        response['code'] = 200
    except Exception as e:
        response['data'] = ''
        response['message'] = str(e)
        response['code'] = 400
    return Response(response)


@api_view(['GET'])
def get_scene(request):
    response = {}
    try:
        scene = Scene.objects.get(id=request.GET.get('id'))
        serializer = SceneSerializerO(scene)
        response['data'] = serializer.data
        response['message'] = "Success"
        response['code'] = 200
        return Response(response)
    except Scene.DoesNotExist as e:
        response['data'] = ''
        response['message'] = str(e)
        response['code'] = 404
    return Response(response)


@api_view(['GET'])
def get_scene_display(request):
    response = {}
    try:
        scene = Scene.objects.get(id=request.GET.get('id'))
        serializer = SceneSerializerDisplay(scene)
        response['data'] = serializer.data
        response['message'] = "Success"
        response['code'] = 200
        return Response(response)
    except Scene.DoesNotExist as e:
        response['data'] = ''
        response['message'] = str(e)
        response['code'] = 404
    return Response(response)


@api_view(['PUT'])
def update_scene(request):
    response = {}
    try:
        put = QueryDict(request.body)
        put_str = list(put.items())[0][0]   # 将获取的QueryDict对象转换为str 类型
        put_dict = eval(put_str)            # 将str类型转换为字典类型
        scene_id = put_dict.get("id")       # 获取传递参数

        scene = Scene.objects.get(id=scene_id)
        serializer = SceneSerializer(scene, data=request.data)
        if serializer.is_valid():
            serializer.save()
            response['data'] = serializer.data
            response['message'] = "Success"
            response['code'] = 200
        else:
            response['data'] = ''
            response['message'] = "Failed"
            response['code'] = 400
    except Scene.DoesNotExist as e:
        response['data'] = ''
        response['message'] = str(e)
        response['code'] = 404
    return Response(response)


@api_view(['DELETE'])
def delete_scene(request):
    response = {}
    try:
        scene = Scene.objects.get(id=request.GET.get('id'))
        scene.delete()
        response['data'] = ""
        response['message'] = "Success"
        response['code'] = 200
    except Scene.DoesNotExist as e:
        response['data'] = ''
        response['message'] = str(e)
        response['code'] = 404
    return Response(response)


@api_view(['DELETE'])
def delete_scene_all(request):
    response = {}
    try:
        scenes = Scene.objects.filter()
        scenes.delete()
        response['data'] = ""
        response['message'] = "Success"
        response['code'] = 200
    except Scene.DoesNotExist as e:
        response['data'] = ''
        response['message'] = str(e)
        response['code'] = 404
    return Response(response)


@api_view(['GET'])
def download_train(request):
    file = open('static/files/files.rar', 'rb')
    response = FileResponse(file)
    response['Content-Type'] = 'application/octet-stream'
    response['Content-Disposition'] = 'attachment;filename="BatchPayTemplate.xls"'
    return response


@api_view(['GET'])
def start_train(request):
    response = {}
    try:
        scene = Scene.objects.get(id=request.GET.get('id'))
    except Scene.DoesNotExist as e:
        response['data'] = ''
        response['message'] = str(e)
        response['code'] = 404
        return Response(response)

    try:
        thread1 = MyThread(request, stubs.start_train, scene)
        thread1.start()
        scene.status = 1
        scene.save()
        response['data'] = ''
        response['message'] = '开始训练'
        response['code'] = 200
    except Exception as e:
        print(e)
        response['data'] = ''
        response['message'] = str(e)
        response['code'] = 400
    return Response(response)


@api_view(['GET'])
def get_train_result(request):
    response = {}
    try:
        scene = Scene.objects.get(id=request.GET.get('id'))
    except Scene.DoesNotExist as e:
        response['data'] = ''
        response['message'] = str(e)
        response['code'] = 404
        return Response(response)

    try:
        result_url = stubs.result_dis(scene.result_storage_path)
        response['data'] = {"url": result_url}
        response['message'] = '获取视图成功'
        response['code'] = 200
    except Exception as e:
        response['data'] = ''
        response['message'] = str(e)
        response['code'] = 400
    return Response(response)


class MyThread(threading.Thread):

    def __init__(self, request, func, param):
        super(MyThread, self).__init__()
        self.request = request
        self.func = func
        self.param = param
        self.result = None

    def run(self):
        serializer = SceneSerializerDisplay(self.param)
        content = serializer.data
        time_start = time.time()
        print(content)
        try:
            self.result = self.func(content)
            print(self.result)
            time_end = time.time()
            seconds = time_end - time_start
            self.param.study_time = self.param.study_time + seconds
            # m, s = divmod(seconds, 60)
            # h, m = divmod(m, 60)
            # str_time = f"{int(h)}小时{int(m)}分{int(s)}秒"
            self.param.status = 2   # 已完成
            print("训练完成")
        except Exception as e:
            self.param.status = 3  # 训练异常
            time_end = time.time()
            seconds = time_end - time_start
            self.param.study_time = self.param.study_time + seconds
            print("训练异常")
            print(str(e))
        self.param.save()
