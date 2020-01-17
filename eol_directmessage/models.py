# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models
from django.contrib.auth.models import User

class EolMessage(models.Model):
    
    course_id = models.CharField(max_length=50)
    sender_user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="sender_user")
    receiver_user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="receiver_user")
    text = models.TextField()
    viewed = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    deleted_at = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return '[%s](%s) %s -> %s' % (self.created_at, self.course_id, self.sender_user.username, self.receiver_user.username)