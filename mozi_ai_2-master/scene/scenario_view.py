from rest_framework import generics

from django.views.decorators.csrf import csrf_exempt
from scene.models import Scenario
from scene.serializers import ScenarioSerializer, ScenarioSerializerO
from rest_framework.decorators import api_view
from rest_framework.response import Response


class AddScenario(generics.CreateAPIView):
    queryset = Scenario.objects.all()
    serializer_class = ScenarioSerializer


class ScenarioList(generics.ListAPIView):
    queryset = Scenario.objects.all()
    serializer_class = ScenarioSerializer


@api_view(['GET'])
def scenario_list(request):
    response = {}
    try:
        scenarios = Scenario.objects.all()
        serializer = ScenarioSerializerO(scenarios, many=True)
        response['data'] = serializer.data
        response['message'] = "Success"
        response['code'] = 200
        return Response(response)
    except Scenario.DoesNotExist as e:
        response['data'] = ''
        response['message'] = str(e)
        response['code'] = 404
    return Response(response)


@csrf_exempt
@api_view(['POST'])
def add_scenario(request):

    # print(request.data)
    response = {}
    scenario_name = request.data['scenario_name']
    side_list = request.data['side_list']
    scenario_file = request.FILES.get("scenario_file", None)  # 获取上传的文件，如果没有文件，则默认为None
    scenario_file.mode = 'rb'
    scenario_file_b = scenario_file.read()

    scenario = Scenario(scenario_name=scenario_name, side_list=side_list, scenario_file=scenario_file_b)
    scenario.save()

    response['data'] = ''
    response['message'] = 'Success'
    response['code'] = 200

    return Response(response)
