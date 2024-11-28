# -*- coding: utf-8 -*-
from django.contrib import admin

from .models import EolMessage, EolMessageConfiguration, EolMessageUserConfiguration, EolMessageFilter

admin.site.register(EolMessage)
admin.site.register(EolMessageConfiguration)
admin.site.register(EolMessageUserConfiguration)
admin.site.register(EolMessageFilter)
