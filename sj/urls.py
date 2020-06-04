from django.urls import path

from . import views


app_name = 'sj'

urlpatterns = [
    path('', views.IndexView.as_view(), name='index'),
    path('<int:pk>/', views.SubnetDetailView.as_view(), name='subnetdetail'),
    path('requestsubnet/<int:wantlen>/<int:wantvers>', views.requestsubnet),
    path('tree',views.SubnetTreeView.as_view(), name='tree')
]
