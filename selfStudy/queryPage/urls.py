from django.urls import path
from . import views

app_name='queryPage'
urlpatterns = [
    path('',views.index,name='home'),
    path('data/',views.data,name='data'),
    path('query/',views.query,name='query'),
    path('search/',views.search,name='search'),
    path('searchAPI/',views.searchApi,name='searchAPI'),
    path('detail/',views.detail,name='detail'),
    path('detailAPI/',views.detailAPI,name='detailAPI')
]