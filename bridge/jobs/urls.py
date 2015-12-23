from django.conf.urls import url
from jobs import views


urlpatterns = [
    url(r'^$', views.tree_view, name='tree'),
    url(r'^(?P<job_id>[0-9]+)/$', views.show_job, name='job'),
    url(r'^downloadfile/(?P<file_id>[0-9]+)/$', views.download_file, name='download_file'),
    url(r'^prepare_run/(?P<job_id>[0-9]+)/$', views.prepare_decision, name='prepare_run'),

    # For ajax requests
    url(r'^ajax/save_view/$', views.save_view),
    url(r'^ajax/remove_view/$', views.remove_view),
    url(r'^ajax/preferable_view/$', views.preferable_view),
    url(r'^ajax/check_view_name/$', views.check_view_name),
    url(r'^ajax/removejobs/$', views.remove_jobs),
    url(r'^ajax/editjob/$', views.edit_job),
    url(r'^ajax/create/$', views.copy_new_job),
    url(r'^ajax/savejob/$', views.save_job),
    url(r'^ajax/showjobdata/$', views.showjobdata),
    url(r'^ajax/upload_file/$', views.upload_file),
    url(r'^ajax/downloadjob/(?P<job_id>[0-9]+)/$', views.download_job),
    url(r'^ajax/downloadjobs/$', views.download_jobs),
    url(r'^ajax/check_access/$', views.check_access),
    url(r'^ajax/upload_job/(?P<parent_id>.*)/$', views.upload_job),
    url(r'^ajax/getfilecontent/$', views.getfilecontent),
    url(r'^ajax/getversions/$', views.get_job_versions),
    url(r'^ajax/remove_versions/$', views.remove_versions),
    url(r'^ajax/stop_decision/$', views.stop_decision),
    url(r'^ajax/run_decision/$', views.run_decision),
    url(r'^ajax/fast_run_decision/$', views.fast_run_decision),
    url(r'^ajax/get_job_data/$', views.get_job_data),

    # For Klever Core
    url(r'^decide_job/$', views.decide_job),
]