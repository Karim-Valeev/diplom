from django.contrib import admin

from app.models import Recognition, User, Video

admin.site.register(User)
admin.site.register(Video)
admin.site.register(Recognition)
