import calendar
from collections import defaultdict
import datetime
import json
from django.forms import DurationField, FloatField
from django.http import JsonResponse
import pandas as pd
import pytz
from .serializers import TaskDurationSerializer
import isodate
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.views.decorators.csrf import csrf_exempt
from django.utils.dateparse import parse_datetime
from django.utils import timezone
from datetime import timedelta
from datetime import datetime 
from .models import TaskEntries, UserProfile, LoginRecord  # Import both models

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


@csrf_exempt
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

            # Get the current date (without time)
            today = timezone.now().date()

            # Filter tasks for the user where the task start_time or end_time is today
            tasks = TaskEntries.objects.filter(user=user, created_on__date=today).order_by('start_time')

            # Prepare tasks as a list of dictionaries
            tasks_list = []
            for task in tasks:
                # Parse and format total_duration if it exists
                if task.total_duration:
                    # Parse the ISO 8601 duration (e.g., 'P0DT00H30M00S') to a timedelta object
                    total_duration_formatted = str(task.total_duration)
                else:
                    total_duration_formatted = None

                tasks_list.append({
                    'id': task.id,
                    'event_type': task.event_type,
                    'start_time': task.start_time.strftime('%I:%M %p'),  # Format as 'HH:MM AM/PM'
                    'end_time': task.end_time.strftime('%I:%M %p'),      # Format as 'HH:MM AM/PM'
                    'task': task.task,
                    'total_duration': total_duration_formatted,         # Include formatted total_duration
                    'status': task.status,
                    'created_on': task.created_on,
                    'modified_on': task.modified_on
                })

            return JsonResponse({'tasks': tasks_list}, status=200)

        except UserProfile.DoesNotExist:
            return JsonResponse({'error': 'User not found'}, status=404)
    else:
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
from django.db.models import Func, F

def get_monthly_reports(request):
    """Handle GET requests to return monthly task reports."""
    if request.method == 'GET':
        try:
            today = timezone.now()
            four_months_ago = today - timedelta(days=120)  # Approximate four months

            # Fetch tasks from the last four months, ensuring not to include future dates
            tasks = TaskEntries.objects.filter(
                created_on__gte=four_months_ago,
                created_on__lt=today
            ).order_by('user', 'created_on')

            # Prepare a dictionary to hold tasks by month and date
            monthly_reports = defaultdict(lambda: defaultdict(lambda: defaultdict(lambda: {'total_duration': timedelta(), 'entry_count': 0})))

            # Loop through tasks and organize them by month and date
            for task in tasks:
                if task.created_on:
                    month_name = task.created_on.strftime('%B').lower()
                    date_str = task.created_on.strftime('%Y-%m-%d')
                    user_id = task.user.id
                    
                    # Accumulate total duration and count entries
                    monthly_reports[month_name][date_str][user_id]['total_duration'] += task.total_duration
                    monthly_reports[month_name][date_str][user_id]['entry_count'] += 1

            # Prepare the final response structure with zero entries for users on each date
            final_reports = []
            users = UserProfile.objects.all()  # Get all users for 'No entries' handling

            for month in monthly_reports.keys():  # Only iterate over existing months
                month_data = {'month': month, 'data': []}
                
                # Get the month number for the current month
                month_number = list(calendar.month_name).index(month.capitalize())
                max_days = calendar.monthrange(today.year, month_number)[1]  # Get max days in the month

                # Generate dates for the current month
                for day in range(1, max_days + 1):
                    date_str = f"{today.year}-{month_number:02d}-{day:02d}"  # Format date as 'YYYY-MM-DD'
                    day_entries = monthly_reports[month].get(date_str, {})

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
                                'total_duration': total_duration_to_string(data['total_duration']),
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

                    month_data['data'].append({
                        'date': date_str,
                        'entries': day_entries_list
                    })

                final_reports.append(month_data)

            return JsonResponse({'month_wise_reports': final_reports}, status=200)

        except Exception as e:
            logger.error(f"Error occurred: {str(e)}")
            return JsonResponse({'error': 'An error occurred while processing the request.'}, status=500)
    else:
        return JsonResponse({'error': 'GET method required'}, status=405)
    
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