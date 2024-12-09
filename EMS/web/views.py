import calendar
from collections import defaultdict
import datetime
import json
from django.forms import DurationField, FloatField
from django.http import HttpResponse, JsonResponse
import pandas as pd
import pytz
from .serializers import ChatMessageSerializer, TaskDurationSerializer
# import isodate
import requests
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.views.decorators.csrf import csrf_exempt
from django.utils.dateparse import parse_datetime
from django.utils import timezone
from datetime import timedelta
from datetime import datetime 
from .models import Chat, TaskEntries, UserProfile, LoginRecord  # Import both models
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated

class LoginView(APIView):
    def post(self, request, *args, **kwargs):
        # Get the username and password from the request
        username = request.data.get('username')
        password = request.data.get('password')

        try:
            # Look up the user by username
            user = UserProfile.objects.get(username=username,password=password)

            # Check if the password matches using check_password method
         
                # Return the user data
            user_data = {
                    'username': user.username,
                    'role': user.get_role_display(),
                    'department': user.get_department_display(),
                    'active_status': user.active_status,
                    'created_at': user.created_at,
                    'id':user.id
                }
            ip_address = request.META.get('REMOTE_ADDR')
            user_agent = request.META.get('HTTP_USER_AGENT')

            # Create and save the login record
            LoginRecord.objects.create(
                user=user,
                login_time=timezone.now(),
                ip_address=ip_address,
                user_agent=user_agent
            )

            return Response(user_data, status=status.HTTP_200_OK)
           

        except UserProfile.DoesNotExist:
            return Response({'error': 'User not found'}, status=status.HTTP_404_NOT_FOUND)

auth_response = None

def authenticate_user():
    global auth_response  # Declare that you want to use the global variable
    url = "https://stemz.attunelive.net/LIMSAPI/api/v1/Authenticate"
    
    payload = {
        'grant_type': 'password',
        'username': 'Phi Sante Diagnostics',
        'password': 'Phi Sante Diagnostics',
        'client_id': 'Phi Sante Diagnostics',
        'client_secret': 'k8M%2FiCmWF6ejbVVpRjhwiVeCtCLwcSW9OUHTvEvKbuciW4GNswV0hYsdyl02AcB%2FFGvAv%2BO9u4ED6ESc08W8212%2BlGnzgn961TzPUuJz7BsYc6mXHTUt8BoOFkZWveP6KI%2F4RpNIxjUdgXWoEMZH3X%2BykVEarZ%2FhLgqJ4WkquTQ2b3YKqVhdIcVydVRvBzX9fonvLcADX6IUnltq3DV5wK7WQQrTBzVI9HzrRueV%2Bg13mVeNqgaPGVWObrCQf9UyCXVc74w2AVZ8eQ895cI2dIiBuCByLyku0I0FiTX51V5B%2FvxfOCODPiBaTwuInrkMb0Oj%2F%2BJCQnGo4hqrenjK43nLDURtNyqJ9%2Fi%2B6ZjyGU6vonHRx6BAnwBmSwlzkyJbvs6ORwIrLyt2XBe45sGtmOTZ%2FyespuVjvrFVVVYAYnHwabcRB4bIBzb%2BsarAtXHfnZ849ILj2lAT3GuFAPdd5NJ2EHdakiEUGcst0Ta2kdxfwJc4MGgW2aJ0IJa1UQnMeF6Oe%2By%2BiUL0X42DHrllqqqI19MH%2Fv1t6Fk6Uy1OYV8oXw9E9%2FwejF5hiFtE5p9EVJ9zO7MF8TtnlOfKfGkqrLJC9Qmrg%2F68JSr4L5CBt9LnlCitklo5YaqeqwCoUkImYEJa%2FLAQi9EUzAeMBtiMfCX9fh8MAJtA6%2BE9c44wNOxDXhVdhtTcNRD9BG3lZOLYf2F4zVwv%2FlddNwG7jWxM%2F%2F0pEM2Yh1p4pZ1VJaqHZ4mq8lNhuBZsQaVFfAJozTWY1XgYFKZtf3utvUwpcGiCj9ezOUS3Qg4%2BjZJjTxoq9WY0IOiVXOsJQKwFLLlOG16YTA%3D%3D'
    }

    try:
        response = requests.post(url, data=payload)
        if response.status_code == 200:
            auth_response = response.json()  # Update the global variable
        else:
            auth_response = {
                'error': 'Authentication failed',
                'status_code': response.status_code,
                'message': response.text,
            }
    except requests.RequestException as e:
        auth_response = {'error': 'Request failed', 'details': str(e)}

@csrf_exempt
def authenticate_view(request):
    global auth_response  # Access the global variable
    authenticate_user()  # This updates the global variable
    if 'error' in auth_response:
        return JsonResponse(auth_response, status=auth_response.get('status_code', 400))
    return JsonResponse({'message': 'Authentication successful', 'data': auth_response})

def authenticate_token(request):
    global auth_response  # Access the global variable
    if request.method == 'GET':
        # Ensure that auth_response is not None and contains the access_token
        if auth_response and 'access_token' in auth_response:
            print('Token:', auth_response['access_token'])
            return JsonResponse({'message': 'Token successful', 'data': auth_response['access_token']})
        else:
            return JsonResponse({'error': 'Token not available'}, status=400)

@csrf_exempt
# @permission_classes([IsAuthenticated])
def create_task_entry(request):
        if request.method == 'POST':
                try:
                    data = json.loads(request.body.decode('utf-8'))

                    # Fetch the user based on user_id
                    user_id = data.get('user_id')
                    user = UserProfile.objects.get(id=user_id)

                    # Handle task entry data
                    event_type = data.get('eventType')
                    task = data.get('task')
                    status = data.get('status')

                    # Get current date
                    today = timezone.now().date()

                    # Use the desired timezone (e.g., Asia/Kolkata for +05:30 timezone)
                    tz = pytz.timezone('Asia/Kolkata')

                    # Combine the current date with the provided start and end times
                    start_time_str = data.get('startTime')
                    end_time_str = data.get('endTime')

                    if start_time_str:
                        start_time = datetime.strptime(f"{today} {start_time_str}", "%Y-%m-%d %I:%M %p")
                        start_time = tz.localize(start_time)  # Localize to the specified timezone
                    else:
                        start_time = timezone.now()  # Default to now if not provided

                    if end_time_str:
                        end_time = datetime.strptime(f"{today} {end_time_str}", "%Y-%m-%d %I:%M %p")
                        end_time = tz.localize(end_time)  # Localize to the specified timezone
                    else:
                        end_time = timezone.now()  # Default to now if not provided

                    # Calculate total duration
                    duration = end_time - start_time
                    total_duration = str(timedelta(seconds=duration.total_seconds())).split('.')[0]  # Format to HH:MM:SS

                    # Create and save the TaskEntry
                    task_entry = TaskEntries.objects.create(
                        user=user,
                        event_type=event_type,
                        start_time=start_time,
                        end_time=end_time,
                        task=task,
                        status=status,
                        total_duration=total_duration  # Save total duration in 'HH:MM:SS' format
                    )

                    return JsonResponse({'message': 'Task entry created successfully', 'id': task_entry.id}, status=201)

                except UserProfile.DoesNotExist:
                    return JsonResponse({'error': 'User not found'}, status=404)
                except Exception as e:
                    return JsonResponse({'error': str(e)}, status=400)
                else:
                    return JsonResponse({'error': 'POST method required'}, status=405)

def get_tasks_for_today(request, user_id):
    if request.method == 'GET':
        try:
            # Fetch the user
            user = UserProfile.objects.get(id=user_id)

            # Get the current date (timezone-aware)
            today = timezone.localtime(timezone.now()).date()

            # Filter tasks for the user where the task's created_on is today
            tasks = TaskEntries.objects.filter(user=user, created_on__date=today).order_by('start_time')

            # Initialize total time for today
            total_time_today = timedelta()

            # Prepare tasks as a list of dictionaries
            tasks_list = []
            for task in tasks:
                # Calculate the task duration if start_time and end_time are present
                if task.start_time and task.end_time:
                    # Assuming start_time and end_time are `time` objects, convert them to `datetime` objects
                    start_time = datetime.combine(today, task.start_time)
                    end_time = datetime.combine(today, task.end_time)
                    task_duration = end_time - start_time
                    total_time_today += task_duration
                else:
                    task_duration = None

                # Parse and format total_duration if it exists
                if task.total_duration:
                    total_duration_formatted = str(task.total_duration)
                else:
                    total_duration_formatted = None

                tasks_list.append({
                    'id': task.id,
                    'event_type': task.event_type,
                    'start_time': task.start_time.strftime('%I:%M %p'),  # Format as 'HH:MM AM/PM'
                    'end_time': task.end_time.strftime('%I:%M %p') if task.end_time else None,  # Format as 'HH:MM AM/PM'
                    'task': task.task,
                    'total_duration': total_duration_formatted,  # Include formatted total_duration
                    'status': task.status,
                    'created_on': task.created_on,
                    'modified_on': task.modified_on
                })

            # Format the total time spent today (in hours and minutes)
            total_hours, remainder = divmod(total_time_today.total_seconds(), 3600)
            total_minutes = remainder // 60
            formatted_total_time_today = f'{int(total_hours)}h {int(total_minutes)}m'

            # Include the total time for today in the response
            return JsonResponse({
                'tasks': tasks_list,
                'today_totaltime': formatted_total_time_today  # New field for total time spent today
            }, status=200)

        except UserProfile.DoesNotExist:
            return JsonResponse({'error': 'User not found'}, status=404)
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)

    return JsonResponse({'error': 'GET method required'}, status=405)


@csrf_exempt
def update_task_entry(request, task_id):
    try:
        data = json.loads(request.body.decode('utf-8'))
        task_entry = TaskEntries.objects.get(id=task_id)

        # Update task entry fields
        task_entry.status = data.get('status', task_entry.status)
        task_entry.task = data.get('task', task_entry.task)
        task_entry.event_type = data.get('eventType', task_entry.event_type)

        today = timezone.now().date()
        tz = pytz.timezone('Asia/Kolkata')

        start_time_str = data.get('start_time')  # Corrected key
        end_time_str = data.get('end_time')      # Corrected key

        # Parse start_time if provided
        if start_time_str:
            start_time = datetime.strptime(f"{today} {start_time_str}", "%Y-%m-%d %I:%M %p")
            start_time = tz.localize(start_time)
            task_entry.start_time = start_time

        # Parse end_time if provided
        if end_time_str:
            end_time = datetime.strptime(f"{today} {end_time_str}", "%Y-%m-%d %I:%M %p")
            end_time = tz.localize(end_time)
            task_entry.end_time = end_time


        duration = end_time - start_time
        total_duration = str(timedelta(seconds=duration.total_seconds())).split('.')[0] 
        task_entry.total_duration =total_duration
        task_entry.save()  # Save the changes

        return JsonResponse({'message': 'Task entry updated successfully'}, status=200)

    except TaskEntries.DoesNotExist:
        return JsonResponse({'error': 'Task not found'}, status=404)
    except json.JSONDecodeError:
        return JsonResponse({'error': 'Invalid JSON input'}, status=400)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=400)
    
@csrf_exempt
def delete_task_entry(request, task_id):
    if request.method == 'DELETE':
        try:
            task_entry = TaskEntries.objects.get(id=task_id)
            task_entry.delete()
            return JsonResponse({'message': 'Task entry deleted successfully'}, status=200)
        except TaskEntries.DoesNotExist:
            return JsonResponse({'error': 'Task entry not found'}, status=404)
    else:
        return JsonResponse({'error': 'DELETE method required'}, status=405)
from django.db.models import Sum, F, ExpressionWrapper, DurationField
import logging
logger = logging.getLogger(__name__)
@csrf_exempt



def convert_string_to_timedelta(time_str):
    """Convert a string 'HH:MM' into a timedelta object."""
    try:
        hours, minutes = map(int, time_str.split(':'))
        return timedelta(hours=hours, minutes=minutes)
    except ValueError:
        logger.error(f"Invalid time format for string: {time_str}")
        return timedelta()  # Return 0 timedelta on error

def total_duration_to_string(duration):
    """Convert timedelta to a string representation."""
    if duration is None or duration.total_seconds() <= 0:
        return "No entries"
    total_seconds = int(duration.total_seconds())
    hours, remainder = divmod(total_seconds, 3600)
    minutes, _ = divmod(remainder, 60)
    return f"{hours} hour{'s' if hours != 1 else ''}, {minutes} min{'s' if minutes != 1 else ''}"


def get_tasks_for_last_week(request, user_id):
    if request.method == 'GET':
        try:
            # Fetch the user
            user = UserProfile.objects.get(id=user_id)

            # Get the current date
            today = timezone.now().date()

            # Get the start date of the past week
            start_date = today - timezone.timedelta(days=7)

            # Filter tasks for the user within the last week, sorted by start_time
            tasks = TaskEntries.objects.filter(
                user=user,
                created_on__date__gte=start_date,
                created_on__date__lte=today
            ).order_by('created_on', 'start_time')  # Order by creation date and start time within each day

            # Prepare tasks as a dictionary grouped by date
            tasks_grouped_by_date = defaultdict(list)
            for task in tasks:
                # Format the date in 'DD-MM-YY' format
                task_date = task.created_on.strftime('%d-%m-%y')

                # Parse and format total_duration if it exists
                total_duration_formatted = str(task.total_duration) if task.total_duration else None

                tasks_grouped_by_date[task_date].append({
                    'id': task.id,
                    'event_type': task.event_type,
                    'start_time': task.start_time.strftime('%I:%M %p'),  # Format as 'HH:MM AM/PM'
                    'end_time': task.end_time.strftime('%I:%M %p'),      # Format as 'HH:MM AM/PM'
                    'task': task.task,
                    'total_duration': total_duration_formatted,         # Include formatted total_duration
                    'status': task.status,
                    'created_on': task.created_on.isoformat(),          # Include ISO 8601 format
                    'modified_on': task.modified_on.isoformat()
                })

            # Include all dates from start_date to today and handle no entries case
            all_dates = [(start_date + timezone.timedelta(days=i)).strftime('%d-%m-%y') for i in range((today - start_date).days + 1)]
            final_tasks = {}
            for date in all_dates:
                if date in tasks_grouped_by_date:
                    final_tasks[date] = tasks_grouped_by_date[date]
                else:
                    # If no tasks for the date, add a "No entries" message
                    final_tasks[date] = [{"message": "No entries"}]

            # Function to sort by date in the format DD-MM-YY
            def date_sort_key(date_string):
                return datetime.strptime(date_string, '%d-%m-%y')

            # Sort the dates to have today on top and earlier dates below in descending order
            sorted_tasks = dict(sorted(final_tasks.items(), key=lambda x: date_sort_key(x[0]), reverse=True))

            return JsonResponse({'tasks': sorted_tasks}, status=200)

        except UserProfile.DoesNotExist:
            return JsonResponse({'error': 'User not found'}, status=404)
    else:
        return JsonResponse({'error': 'GET method required'}, status=405)


from django.db.models import Func, F
def get_monthly_reports(request):
    """Handle GET requests to return monthly task reports."""
    if request.method == 'GET':
        try:
            # Get the month parameter from the request, default to current month if not provided
            month = request.GET.get('month', None)
            today = timezone.now()

            # Determine the current month if not provided
            if month is None:
                month_number = today.month
            else:
                # Get the month number based on the month name
                month_number = list(calendar.month_name).index(month.capitalize())
                if month_number == 0:
                    return JsonResponse({'error': 'Invalid month name'}, status=400)

            # Define start and end dates for the selected month
            start_date = today.replace(month=month_number, day=1)
            end_date = (start_date + timedelta(days=31)).replace(day=1)  # Start of next month

            # Fetch tasks for the selected month
            tasks = TaskEntries.objects.filter(
                created_on__gte=start_date,
                created_on__lt=end_date
            ).order_by('user', 'created_on')

            # Prepare a dictionary to hold tasks by date and user
            monthly_reports = defaultdict(lambda: defaultdict(lambda: {'total_duration': timedelta(), 'entry_count': 0}))

            # Loop through tasks and organize them by date
            for task in tasks:
                if task.created_on:
                    date_str = task.created_on.strftime('%Y-%m-%d')
                    user_id = task.user.id

                    # Accumulate total duration and count entries
                    monthly_reports[date_str][user_id]['total_duration'] += task.total_duration
                    monthly_reports[date_str][user_id]['entry_count'] += 1

            # Get all users for 'No entries' handling
            users = UserProfile.objects.all()

            # Prepare the final report
            final_report = {
                'month': calendar.month_name[month_number],
                'data': []
            }

            # Generate dates for the month
            max_days = calendar.monthrange(today.year, month_number)[1]  # Get max days in the month

            for day in range(1, max_days + 1):
                date_str = f"{today.year}-{month_number:02d}-{day:02d}"  # Format date as 'YYYY-MM-DD'
                day_entries = monthly_reports.get(date_str, {})

                # Create a list to store entries for each user
                day_entries_list = []

                # Populate entries for each user
                for user in users:
                    if user.id in day_entries:
                        # User has entries for this date
                        data = day_entries[user.id]
                        day_entries_list.append({
                            'user_id': user.id,
                            'username': user.username,
                            'total_duration': total_duration_to_string(data['total_duration']),  # Convert timedelta to string
                            'entry_count': data['entry_count']
                        })
                    else:
                        # User has no entries for this date
                        day_entries_list.append({
                            'user_id': user.id,
                            'username': user.username,
                            'total_duration': "No entries",
                            'entry_count': 0
                        })

                final_report['data'].append({
                    'date': date_str,
                    'entries': day_entries_list
                })

            return JsonResponse({'month_wise_reports': [final_report]}, status=200)

        except Exception as e:
            logger.error(f"Error occurred: {str(e)}")
            return JsonResponse({'error': 'An error occurred while processing the request.'}, status=500)
    else:
        return JsonResponse({'error': 'GET method required'}, status=405)

def total_duration_to_string(duration):
    """Convert timedelta to a string representation."""
    total_seconds = int(duration.total_seconds())
    hours, remainder = divmod(total_seconds, 3600)
    minutes, seconds = divmod(remainder, 60)
    return f"{hours}h {minutes}m" if hours else f"{minutes}m"
def total_duration_to_string(duration):
    """Convert timedelta to a string representation."""
    total_seconds = int(duration.total_seconds())
    hours, remainder = divmod(total_seconds, 3600)
    minutes, seconds = divmod(remainder, 60)
    return f"{hours}h {minutes}m" if hours else f"{minutes}m"


def get_month_wise_user_percentage(request):
    if request.method == 'GET':
        try:
            # Get the current date
            today = timezone.now()
            # Get the first day of the current month
            first_day_of_current_month = today.replace(day=1)

            # Initialize dictionaries for total durations per user and month
            user_month_total_duration = defaultdict(lambda: defaultdict(timedelta))
            total_month_duration = defaultdict(timedelta)  # Total duration for each month

            # Get all users
            users = UserProfile.objects.all()
            user_names = {user.id: user.username.lower() for user in users}  # Store user names for response

            # Iterate through each user
            for user in users:
                user_id = user.id

                # Iterate through the last four months
                for month_offset in range(4):
                    # Calculate the month
                    month_start = (first_day_of_current_month - pd.DateOffset(months=month_offset))
                    month_end = month_start + pd.DateOffset(months=1)

                    # Get tasks for the specific month
                    tasks = TaskEntries.objects.filter(
                        user=user,
                        created_on__range=(month_start, month_end)
                    )

                    # Sum up the total_duration for the tasks
                    total_duration = tasks.aggregate(Sum('total_duration'))['total_duration__sum'] or timedelta(0)
                    user_month_total_duration[user_id][month_start.strftime('%B')] += total_duration

                    # Add to the total duration for the month
                    total_month_duration[month_start.strftime('%B')] += total_duration

            # Prepare the result in a structured format
            results = defaultdict(dict)
            for user in users:
                user_name = user.username.lower()  # Get the username in lowercase

                # Prepare monthly percentages for the user
                for month_offset in range(4):
                    month_name = (first_day_of_current_month - pd.DateOffset(months=month_offset)).strftime('%B')
                    total_duration = user_month_total_duration[user.id][month_name]

                    # Calculate the percentage for this month
                    if total_month_duration[month_name] > timedelta(0):  # Avoid division by zero
                        percentage = (total_duration.total_seconds() / total_month_duration[month_name].total_seconds()) * 100
                    else:
                        percentage = 0

                    if percentage > 0:  # Only include users with a percentage greater than 0
                        results[month_name][user_name] = round(percentage, 2)  # Store the rounded percentage

            # Convert results to a more readable format
            formatted_results = {month: dict(users) for month, users in results.items()}

            return JsonResponse({'month_wise_user_percentage': formatted_results}, status=200)

        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)
    else:
        return JsonResponse({'error': 'GET method required'}, status=405)
    
def pacs(request):
    
    return JsonResponse({'error': 'GET method required'}, status=405)

def get_tasks_for_today_user_report(request):
    if request.method == 'GET':
        try:
            # Get the current date (timezone-aware)
            today = timezone.localdate()

            # Filter tasks for all users where the task created_on is today
            tasks = TaskEntries.objects.filter(created_on__date=today).order_by('user', 'start_time')

            # Prepare a dictionary where tasks are grouped by user
            user_tasks = {}
            for task in tasks:
                # Parse and format total_duration if it exists
                total_duration_formatted = str(task.total_duration) if task.total_duration else None

                # Fallback if start_time or end_time is missing
                start_time = task.start_time.strftime('%I:%M %p') if task.start_time else None
                end_time = task.end_time.strftime('%I:%M %p') if task.end_time else None

                # Get the username for grouping
                username = task.user.username

                # Initialize user's task list if not already in the dictionary
                if username not in user_tasks:
                    user_tasks[username] = []

                # Append task details to the user's task list
                user_tasks[username].append({
                    'id': task.id,
                    'event_type': task.event_type,
                    'start_time': start_time,  # Format as 'HH:MM AM/PM'
                    'end_time': end_time,      # Format as 'HH:MM AM/PM'
                    'task': task.task,
                    'total_duration': total_duration_formatted,  # Include formatted total_duration
                    'status': task.status,
                    'created_on': task.created_on,
                    'modified_on': task.modified_on
                })

            return JsonResponse({'user_tasks': user_tasks}, status=200)

        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)
    else:
        return JsonResponse({'error': 'GET method required'}, status=405)
    

        
    

   
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas





def generate_pdf(request):
    # Sample JSON data (this would come from your actual API)
    data = {
        "month_wise_user_percentage": {
            "October": {
                "jerry": 28.36,
                "dev": 28.0,
                "samsul": 43.64
            },
            "September": {
                "jerry": 22.02,
                "dev": 1.75,
                "qa": 33.88,
                "samsul": 42.35
            }
        }
    }

    # Create the HttpResponse object with PDF headers
    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = 'attachment; filename="month_wise_user_percentage.pdf"'

    # Create the PDF object
    p = canvas.Canvas(response, pagesize=letter)

    # Set starting position
    y = 750

    # Write data to PDF
    p.drawString(100, y, "Month-wise User Percentage")
    y -= 30

    for month, users in data['month_wise_user_percentage'].items():
        p.drawString(100, y, f"Month: {month}")
        y -= 20
        for user, percentage in users.items():
            p.drawString(120, y, f"{user}: {percentage}%")
            y -= 20
        y -= 10

    # Finalize the PDF
    p.showPage()
    p.save()

    return response

# Chat
from rest_framework import generics
class ChatMessageListCreate(generics.ListCreateAPIView):
    serializer_class = ChatMessageSerializer

    def get_queryset(self):
        user_id = self.request.query_params.get('user_id')  # Get user_id from the request
        if user_id:
            return Chat.objects.filter(user_id=user_id).order_by('timestamp')
        return Chat.objects.none()  # Return no messages if no user_id is provided

    def perform_create(self, serializer):
        serializer.save(user_id=self.request.data.get('user_id'))




    