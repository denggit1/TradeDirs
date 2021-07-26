from django.conf.urls import url, include
from . import views

urlpatterns = [
    url(r'^$', views.index),
    url(r'^login/$', views.login),
    url(r'^delsession/$', views.delSession),
    url(r'^set_cookie/$', views.set_cookie),
    url(r'^eth_data/$', views.eth_data),
    url(r'^key_time/$', views.key_time),
    url(r'^sign/$', views.sign),
    url(r'^ws_tick/$', views.ws_tick),
    url(r'^senior/$', views.senior),
    url(r'^freq_info/$', views.freq_info),
    url(r'^ps_aux/$', views.ps_aux),
    url(r'^capitalcurve/$', views.capitalcurve),
    url(r'^bnwh/$', views.bnwh),
    url(r'^bnod/$', views.bnod),
    url(r'^count$', views.get_count),
    url(r'^status$', views.get_status),
    url(r'^bdd$', views.bdd),
    #url(r'^api_info/$', views.api_info),
    #url(r'^mt4_update/$', views.mt4_update),
]
