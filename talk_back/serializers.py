from rest_framework import serializers
from talk_back import models

class BranchEventDataSerializer(serializers.Serializer):

	def perform_tasks_and_get_data(self, data):
		models.BranchEventData.objects.create(event_data=data)
		return {'status': 'success'}
