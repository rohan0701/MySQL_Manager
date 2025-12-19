"""
URL configuration for mysql_manager project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path
from mysqli import views

urlpatterns = [
    path('admin/', admin.site.urls),
    path('login/',views.login), 
    path('home/',views.home),
    path('explore/',views.explore),
    path('get_dbs/',views.get_dbs),
    path('create_dbs/',views.create_dbs),
    path('delete_dbs/',views.delete_dbs),
    path('work/',views.work),
    path('select_db/',views.select_db),
    path('show_tables/',views.show_tables),
    path('view_table/', views.view_table),
    path('create_table/',views.create_table),
    path('delete_table/',views.delete_table),
    path('edit_table/',views.edit_table),
    path('insert/',views.insert),
    path('insert_records/',views.insert),
    path('update_records/',views.update_records),
    path('delete_record/',views.delete_record),
]
