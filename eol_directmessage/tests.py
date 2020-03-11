# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from openedx.core.lib.tests.tools import assert_true
from mock import patch, Mock


from django.test import TestCase, Client
from django.urls import reverse

from util.testing import UrlResetMixin
from xmodule.modulestore import ModuleStoreEnum
from xmodule.modulestore.tests.django_utils import ModuleStoreTestCase

from xmodule.modulestore.tests.factories import CourseFactory
from student.tests.factories import UserFactory, CourseEnrollmentFactory

import views

from models import EolMessage, EolMessageConfiguration, EolMessageUserConfiguration

USER_COUNT = 11

class TestDirectMessage(UrlResetMixin, ModuleStoreTestCase):
    def setUp(self):

        super(TestDirectMessage, self).setUp()

        # create a course
        self.course = CourseFactory.create(org='mss', course='999',
                                           display_name='eol directmessage course')

        # Patch the comment client user save method so it does not try
        # to create a new cc user when creating a django user
        with patch('student.models.cc.User.save'):
            uname = 'student'
            email = 'student@edx.org'
            password = 'test'

            # Create the student
            self.main_student = UserFactory(username=uname, password=password, email=email)

            # Enroll the student in the course
            CourseEnrollmentFactory(user=self.main_student, course_id=self.course.id)

            # Log the student in
            self.main_client = Client()
            assert_true(self.main_client.login(username=uname, password=password))
        
        # Create users and enroll
        self.users = [UserFactory.create() for _ in range(USER_COUNT)]
        for user in self.users:
            CourseEnrollmentFactory.create(user=user, course_id=self.course.id)

    def test_render_page(self):
        """
            Test render page with three cases:
                1. User not logged
                2. User logged but not enrolled
                3. User logged and enrolled
        """
        uname = 'student_not_enrolled'
        email = 'student_not_enrolled@edx.org'
        password = 'test'
        url = reverse('directmessage_view',
                      kwargs={'course_id': self.course.id})

        student_not_enrolled = UserFactory(username=uname, password=password, email=email) # Create the student

        # Student without login
        client = Client() 
        response = client.get(url)
        self.assertEqual(response.status_code, 302) # Redirect to login

        # Student logged but not enrolled
        client.login(username=uname, password=password)
        response = client.get(url)
        self.assertEqual(response.status_code, 404) # Show error 404

        # Student logged and enrolled
        CourseEnrollmentFactory(user=student_not_enrolled, course_id=self.course.id)
        response = client.get(url)
        self.assertEqual(response.status_code, 200) # Correct render page

        