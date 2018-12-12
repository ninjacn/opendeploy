from django.contrib import admin
from .models import (Host, HostGroup)

# Register your models here.

@admin.register(Host)
class HostAdmin(admin.ModelAdmin):
    list_display = ('ipaddr', 'hostname', 'created_at', 'updated_at', 'status')
    search_fields = ('ipaddr', 'hostname')

@admin.register(HostGroup)
class HostGroupAdmin(admin.ModelAdmin):
    list_display = ('name', 'created_at', 'updated_at')
    search_fields = ('name',)
    filter_horizontal = ('host',)
