from django.urls import path, include
from django.contrib.auth import views as auth_views
from rest_framework.urlpatterns import format_suffix_patterns
from . import views
from django.contrib import admin


urlpatterns = [
    path("", views.index, name="index"),
    path('tree/', views.tree, name='tree'),
    path('filtered-tree/', views.filtered_tree, name='filtered-tree'),
    path('subnet/', views.get_subnet, name='subnet'),
    path('subnet-list/', views.SubnetListView.as_view(), name='subnet-list'),
    path('labelview-list/', views.LabelValueListView.as_view() , name='labelview-list'),
    path('label/', views.LabelListView.as_view(), name='label-list'),
    path('label/<int:pk>/edit', views.label_value_edit, name='label-edit'),
    path('label/add/', views.label_value_add, name='label-add'),
    path('label/<int:pk>/delete', views.label_delete, name='label-delete'),
    path('tag/', views.TagListView.as_view(), name='tag-list'),
    path('tag/add/', views.tag_value_add, name='tag-add'),
    path('tag/<int:pk>/edit', views.tag_value_edit, name='tag-edit'),
    path('tag/<int:pk>/delete', views.tag_delete, name='tag-delete'),
    path('tagvalue/<int:pk>/delete', views.tag_value_delete, name='tagvalue-delete'),
    path('labelvalue/<int:pk>/delete', views.label_value_delete, name='labelvalue-delete'),
    path("subnet/<int:pk>/", views.edit_subnet, name='edit_subnet'),
    path('subnet/<int:pk>/delete/', views.SubnetDeleteView.as_view()),
    path('home/', views.HomeView.as_view(), name='home'),
    path("api/network/", views.NetworkList.as_view()),
    path("api/network/<int:pk>/", views.NetworkDetail.as_view()),
    path("api/root/", views.RootNode.as_view()),
    path("users/", views.UserList.as_view()),
    path("users/<int:pk>/", views.UserDetail.as_view()),
    path("api-auth/", include("rest_framework.urls")),
    path('tagview/', views.TagFormView.as_view()),
    path( 'success/', views.success_view, name='success'),
    path("test/", views.test),
    path('admin/', admin.site.urls),
    path('accounts/', include('django.contrib.auth.urls')),  # Includes login, logout, password reset paths
    path(route='login/', view=views.LoginView.as_view(), name='login'),
    path('logout/', auth_views.LogoutView.as_view(), name='logout'),
]
urlpatterns = format_suffix_patterns(urlpatterns)