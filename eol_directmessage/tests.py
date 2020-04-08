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
from opaque_keys.edx.keys import CourseKey

from six import text_type
import views

from models import EolMessage, EolMessageConfiguration, EolMessageUserConfiguration

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
        self.assertEqual(len(enrolled_students), USER_COUNT)

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
