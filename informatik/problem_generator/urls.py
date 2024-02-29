# problem_generator/urls.py
from django.urls import path
from . import views

urlpatterns = [
    path('generate/', views.generate_problem, name='generate_problem'),
    path('correct/', views.correct_problem, name='correct_problem'),
    
    path('search_users/', views.search_users, name="search_users"),
    path('send_request/<uuid:user_id>', views.send_friend_request, name="send_request"),
    path('friend_requests/', views.friend_requests, name="friend_requests"),
    path('accept_friend_request/<int:request_id>/', views.accept_friend_request, name='accept_friend_request'),
    path('friends/', views.view_friends, name='view_friends'),

    path('enroll_in_course/', views.enroll_in_course, name='enroll_in_course'),
    path('course_detail/<uuid:course_id>/', views.course_detail, name='course_detail'),  # Add this line
    path('create_course/', views.create_course, name='create_course'),
    path('my_courses/', views.my_courses, name='my_courses'),
    path('create_homework/<uuid:course_id>', views.generate_homework, name="create_homework"),

    path('homework/<int:homework_id>/', views.homework_detail, name='homework_detail'),
    path('homework/<int:homework_id>/submit/', views.submit_homework, name='submit_homework'),

    path('problem/<int:problem_id>/', views.problem_detail, name='problem_detail'),

    path('', views.landingPage, name="landingPage"),

]