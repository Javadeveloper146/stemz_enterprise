from django.urls import path
# from web import views
from .views import LoginView, get_month_wise_user_percentage,get_monthly_reports,create_task_entry,update_task_entry,delete_task_entry,get_tasks_for_today
from web import views

urlpatterns = [
    #  path("", login, name='login'),
    path('login', LoginView.as_view(), name='login'),
    path('api/tasks', create_task_entry, name='create_task'),
    path('api/update-task/<int:task_id>', update_task_entry, name='update_task_entry'),  # URL for updating a task entry
    path('api/delete-task/<int:task_id>', delete_task_entry, name='delete_task_entry'),
    path('api/tasks-user/<int:user_id>', get_tasks_for_today, name='get_tasks_for_today'),
    path('api/task-duration', get_monthly_reports, name='task-duration'),
       path('api/month-wise-total-duration/', get_month_wise_user_percentage, name='month-wise-total-duration'),
]

