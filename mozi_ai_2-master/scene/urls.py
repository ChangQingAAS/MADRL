from django.conf.urls import url
from scene import views, scenario_view, agent_views
from scene import sys_info

urlpatterns = [
    # url(r'add_scenario$', scenario_view.AddScenario.as_view()),
    url(r'add_scenario$', scenario_view.add_scenario),
    url(r'scenario_list$', scenario_view.scenario_list),

    url(r'agent_list$', agent_views.agent_list),
    url(r'add_agent$', agent_views.add_agent),
    url(r'get_agent$', agent_views.get_agent),
    url(r'update_agent$', agent_views.update_agent),
    url(r'update_agent_file$', agent_views.update_agent_file),
    url(r'delete_agent$', agent_views.delete_agent),
    url(r'download_agent$', agent_views.download_agent),

    url(r'add_scene$', views.add_scene),
    url(r'get_scene$', views.get_scene),
    url(r'get_scene_display$', views.get_scene_display),
    url(r'show_scenes$', views.show_scenes),
    url(r'update_scene$', views.update_scene),
    url(r'delete_scene$', views.delete_scene),
    url(r'delete_scene_all$', views.delete_scene_all),

    url(r'start_train$', views.start_train),
    url(r'get_train_result$', views.get_train_result),
    url(r'download_train$', views.download_train),
    url(r'get_sys_info_all$', sys_info.get_sys_info_all),
    url(r'update_agent_2$', views.UpdateAgent.as_view()),
]
