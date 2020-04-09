# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from openedx.core.lib.tests.tools import assert_true
from mock import patch, Mock


from django.test import TestCase, Client
from django.urls import reverse
from openedx.core.djangoapps.site_configuration.tests.test_util import (
    with_site_configuration,
    with_site_configuration_context,
)

from util.testing import UrlResetMixin
from xmodule.modulestore import ModuleStoreEnum
from xmodule.modulestore.tests.django_utils import ModuleStoreTestCase

from xmodule.modulestore.tests.factories import CourseFactory
from student.tests.factories import UserFactory, CourseEnrollmentFactory
from lms.djangoapps.courseware.tests.factories import StaffFactory
from student.roles import CourseInstructorRole, CourseStaffRole
from opaque_keys.edx.keys import CourseKey

from six import text_type
import views

import json

from models import EolMessage, EolMessageConfiguration, EolMessageUserConfiguration, EolMessageFilter

from openedx.core.djangoapps.site_configuration import helpers as configuration_helpers

USER_COUNT = 11


class TestDirectMessage(UrlResetMixin, ModuleStoreTestCase):
    def setUp(self):

        super(TestDirectMessage, self).setUp()

        # create a course
        self.course = CourseFactory.create(
            org='mss', course='999', display_name='eol directmessage course')

        # Patch the comment client user save method so it does not try
        # to create a new cc user when creating a django user
        with patch('student.models.cc.User.save'):
            uname = 'student'
            email = 'student@edx.org'
            password = 'test'

            # Create the student
            self.main_student = UserFactory(
                username=uname, password=password, email=email)

            # Enroll the student in the course
            CourseEnrollmentFactory(
                user=self.main_student,
                course_id=self.course.id)

            # Log the student in
            self.main_client = Client()
            assert_true(
                self.main_client.login(
                    username=uname,
                    password=password))

            # Create and Enroll staff user
            self.staff_user = UserFactory(username='staff_user', password='test', email='staff@edx.org', is_staff=True)
            CourseEnrollmentFactory(user=self.staff_user, course_id=self.course.id)

            role_staff = CourseStaffRole(self.course.id)
            role_staff.add_users(self.staff_user)

            # Log the user staff in
            self.staff_client = Client()
            assert_true(self.staff_client.login(username='staff_user', password='test'))

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
        uname = 'test_student'
        email = 'test_student@edx.org'
        password = 'test'
        url = reverse('directmessage_view',
                      kwargs={'course_id': self.course.id})

        test_student = UserFactory(
            username=uname,
            password=password,
            email=email)  # Create the student

        # Student without login
        client = Client()
        response = client.get(url)
        self.assertEqual(response.status_code, 302)  # Redirect to login

        # Student logged but not enrolled
        client.login(username=uname, password=password)
        response = client.get(url)
        self.assertEqual(response.status_code, 404)  # Show error 404

        # Student logged and enrolled
        CourseEnrollmentFactory(user=test_student, course_id=self.course.id)
        response = client.get(url)
        self.assertEqual(response.status_code, 200)  # Correct render page

    def test_get_all_students(self):
        """
            Test _get_all_students function. It returns an array of users (without logged user).
        """
        enrolled_students = views._get_all_students(
            self.main_student.id, text_type(self.course.id))
        # Check length of enrolled students without logged user
        self.assertEqual(len(enrolled_students), USER_COUNT+1) # +1 -> Staff User

    def test_get_user_configuration(self):
        """
            Test get_user_configuration. At the moment only is_muted attribute
            Three cases:
                1. Without configuration
                2. With is_muted true
                3. With is_muted false
        """
        config = views._get_user_configuration(
            self.main_student, self.course.id)  # Without configuration
        self.assertEqual(config['is_muted'], False)

        user_config = EolMessageUserConfiguration.objects.create(
            user_id=self.main_student.id,
            course_id=self.course.id
        )
        # With is_muted true (default when create)
        config = views._get_user_configuration(
            self.main_student, self.course.id)
        self.assertEqual(config['is_muted'], True)

        user_config.is_muted = False
        user_config.save()
        config = views._get_user_configuration(
            self.main_student, self.course.id)  # With is_muted false
        self.assertEqual(config['is_muted'], False)

    
    def test_get_only_staff_filter(self):
        """
            Test get only staff filter with staff user and student.
            Test Priority:
                1. Staff user: always 'False'
                2. Student user: Models > Site Configurations > Default value ('False')
        """
        # Test staff_user always return False
        only_staff_filter = views._get_only_staff_filter(self.staff_user, self.course)
        self.assertEqual(only_staff_filter, False)

        # Test student. By default (without any configuration) return False
        only_staff_filter = views._get_only_staff_filter(self.main_student, self.course)
        self.assertEqual(only_staff_filter, False)

        # Test with configurations
        
        # Test student with site configuration (only_staff)
        test_config = {
            'EOL_DIRECTMESSAGE_ONLY_STAFF' : True,
        }
        with with_site_configuration_context(configuration=test_config):
            only_staff_filter = views._get_only_staff_filter(self.main_student, self.course)
            self.assertEqual(only_staff_filter, True)

            # Test student with site and course configuration (in models)
            course_filter = EolMessageFilter.objects.create(
                course_id=self.course.id,
                only_staff=False,
            )
            only_staff_filter = views._get_only_staff_filter(self.main_student, self.course)
            self.assertEqual(only_staff_filter, False)

            course_filter.only_staff = True
            course_filter.save()
            only_staff_filter = views._get_only_staff_filter(self.main_student, self.course)
            self.assertEqual(only_staff_filter, True)

            only_staff_filter = views._get_only_staff_filter(self.staff_user, self.course)
            self.assertEqual(only_staff_filter, False)

    def test_get_student_chats(self):
        """
            Test get_student_chats
        """
        # Without chats return empty array
        response = self.main_client.get(reverse('get_student_chats',kwargs={'course_id': self.course.id}))
        self.assertEqual(response.content, '[]')

        # Create a message
        message = EolMessage.objects.create(
            course_id=self.course.id,
            sender_user=self.main_student,
            receiver_user=self.staff_user,
            text='test_message'
        )

        # With one chat. Message not viewed
        response = self.main_client.get(reverse('get_student_chats',kwargs={'course_id': self.course.id}))
        data = json.loads(response.content)
        self.assertEqual(data[0]['receiver_user__username'], self.staff_user.username)
        self.assertEqual(data[0]['min_viewed'], False)
        self.assertEqual(len(data), 1)

        # Add another user to the chat list
        test_student = UserFactory(
            username='test_student',
            password='test_password',
            email='test@mail.mail')  # Create the student
        CourseEnrollmentFactory(user=test_student, course_id=self.course.id)
        new_message = EolMessage.objects.create(
            course_id=self.course.id,
            sender_user=test_student,
            receiver_user=self.main_student,
            text='test_message2'
        )
        response = self.main_client.get(reverse('get_student_chats',kwargs={'course_id': self.course.id}))
        data = json.loads(response.content)
        self.assertEqual(len(data), 2)

    def test_get_access_roles(self):
        """
            Test get access roles in course (staff and instructor)
        """
        roles = views.get_access_roles(text_type(self.course.id))
        self.assertEqual(len(roles), 1)

        # Add instructor user to the course
        instructor = UserFactory.create(password="test")
        role = CourseInstructorRole(self.course.id)
        role.add_users(instructor)
        roles = views.get_access_roles(text_type(self.course.id))
        self.assertEqual(len(roles), 2)