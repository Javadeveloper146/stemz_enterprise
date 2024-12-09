from django.urls import path
# from web import views
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from .views import ChatMessageListCreate, authenticate_token,authenticate_view,create_task_entry, LoginView, generate_pdf, get_monthly_reports, get_tasks_for_last_week, get_tasks_for_today_user_report,get_month_wise_user_percentage, pacs,update_task_entry,delete_task_entry,get_tasks_for_today
from web import views

urlpatterns = [
    #  path("", login, name='login'),
    path('api/token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('api/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('login', LoginView.as_view(), name='login'),
    path('api/tasks', create_task_entry, name='create_task'),
    path('api/update-task/<int:task_id>', update_task_entry, name='update_task_entry'),  # URL for updating a task entry
    path('api/delete-task/<int:task_id>', delete_task_entry, name='delete_task_entry'),
    path('api/tasks-user/<int:user_id>', get_tasks_for_today, name='get_tasks_for_today'),
    path('api/task-duration', get_monthly_reports, name='task-duration'),
     path('api/tasks/one-week-data/<int:user_id>', get_tasks_for_last_week, name='tasks_today_user_oneweek'),
    path('api/month-wise-total-duration/', get_month_wise_user_percentage, name='month-wise-total-duration'),
    path('api/tasks/today', get_tasks_for_today_user_report, name='tasks_today_user_report'),
     path('api/download-monthly-report/', generate_pdf, name='download-monthly-report'),
      path('api/pacs', pacs, name='pacs'),
     path('api/chat/messages/', ChatMessageListCreate.as_view(), name='chat-messages'),
      path('api/authenticate', authenticate_view, name='authenticate_user'),
       path('api/auth', authenticate_token, name='auth'),
      
    # Allocated 
    
    # Review
    
    
]

