"""
URL configuration for simplelms project.

The urlpatterns list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.1/topics/http/urls/
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
from django.urls import path
from lms_core.views import index, testing, addData, editData, deleteData, register, list_comments, user_activity_dashboard, course_analytics, list_course_contents, batch_enroll, moderate_comment, enroll_student, create_announcement, show_announcements, edit_announcement, delete_announcement, create_category, show_category, delete_category, course_certificate, mark_content_completed
from lms_core.api import apiv1
from lms_core.admin import admin_site
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.decorators import user_passes_test
from django.http import JsonResponse


urlpatterns = [
    path('api/v1/', apiv1.urls),
    path('admin/', admin_site.urls),  
    path('testing/', testing),
    path('tambah/', addData),
    path('ubah/', editData),
    path('hapus/', deleteData),
    path('register/', register, name='register'),
    path('batch_enroll/', batch_enroll, name='batch_enroll'),
    path('comments/<int:content_id>/', list_comments, name='list_comments'),
    path('comments/moderate/<int:content_id>/<int:comment_id>/', moderate_comment, name='moderate_comment'),
    path('user_activity/<int:user_id>/', user_activity_dashboard, name='user_activity_dashboard'),
    path('course_analytics/<int:course_id>/', course_analytics, name='course_analytics'),
    path('course_contents/<int:course_id>/', list_course_contents, name='list_course_contents'),
    path('course/enroll_student/', enroll_student, name='enroll_student'),
    path('course/<int:course_id>/announcement/create/', create_announcement, name='create_announcement'),
    path('course/<int:course_id>/announcement/show/', show_announcements, name='show_announcements'),
    path('course/<int:course_id>/announcement/edit/<int:announcement_id>/', edit_announcement, name='edit_announcement'),
    path('announcement/<int:announcement_id>/delete/', delete_announcement, name='delete_announcement'),
    path('category/create/', create_category, name='create_category'),
    path('category/show/', show_category, name='show_category'),
    path('category/<int:category_id>/delete/', delete_category, name='delete_category'),
    path('certificate/<int:user_id>/<int:course_id>/', course_certificate, name='course_certificate'),
    path('content/mark_completed/', mark_content_completed, name='mark_content_completed'),


    path('', index),
]