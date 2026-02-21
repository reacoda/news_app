from django.contrib import admin
from .models import CustomUser, Article, Newsletter, Publisher

# Register models here
admin.site.register(CustomUser)
admin.site.register(Article)
admin.site.register(Newsletter)
admin.site.register(Publisher)
