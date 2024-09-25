
from rest_framework import serializers
from datetime import datetime, time

from datetime import datetime, time

class TaskDurationSerializer(serializers.Serializer):
    username = serializers.CharField(source='user__username')
    role = serializers.CharField(source='user__role')
    user_id = serializers.IntegerField()
    task_date = serializers.DateField(source='created_on__date')
    total_duration_hours = serializers.FloatField()