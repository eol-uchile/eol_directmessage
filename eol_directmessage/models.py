# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError


class EolMessage(models.Model):

    course_id = models.CharField(max_length=50)
    sender_user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="sender_user")
    receiver_user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="receiver_user")
    text = models.TextField()
    viewed = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    deleted_at = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return '[%s](%s) %s -> %s' % (self.created_at, self.course_id,
                                      self.sender_user.username, self.receiver_user.username)


class EolMessageConfiguration(models.Model):
    """
        General configuration
    """
    last_mail = models.DateTimeField(auto_now_add=True)

    def save(self, *args, **kwargs):
        """
            Override save method to have only one EolMessageConfiguration instance
        """
        if not self.pk and EolMessageConfiguration.objects.exists():
            raise ValidationError(
                'There is can be only one EolMessageConfiguration instance')
        return super(EolMessageConfiguration, self).save(*args, **kwargs)

    def __str__(self):
        return '%s' % (self.last_mail)


class EolMessageUserConfiguration(models.Model):
    """
        User configuration
    """
    class Meta:
        index_together = [
            ["user", "course_id"],
        ]
        unique_together = [
            ["user", "course_id"],
        ]

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="user")
    course_id = models.CharField(max_length=50)
    # If is_muted=True the user will not receive reminder mails
    is_muted = models.BooleanField(default=True)

    def __str__(self):
        return '[%s](%s) %s' % (
            self.is_muted, self.course_id, self.user.username)
