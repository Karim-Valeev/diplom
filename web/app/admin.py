from django.contrib import admin

from app.models import User, Video, Recognition

admin.site.register(User)
admin.site.register(Video)
admin.site.register(Recognition)
