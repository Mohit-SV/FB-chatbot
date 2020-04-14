from django.db import models
from django.contrib.postgres.fields import JSONField


class BranchEventData(models.Model):

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    event_data = JSONField(blank=True, null=True)

    class Meta(object):
        db_table = 'branch_event_data'    	
