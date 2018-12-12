from django.contrib import admin
from .models import (Env, Project, Task)

# Register your models here.

@admin.register(Env)
class EnvAdmin(admin.ModelAdmin):
    list_display = ('name', 'comment', 'created_at', 'updated_at')
    search_fields = ('name', 'comment')

@admin.register(Project)
class ProjectAdmin(admin.ModelAdmin):
    list_display = ('title', 'vcs_type', 'repository_url', 'created_at', 'updated_at')
    search_fields = ('title', 'vcs_type', 'repository_url')
    # filter_horizontal = ('host',)

@admin.register(Task)
class TaskAdmin(admin.ModelAdmin):
    list_display = ('project', 'env', 'has_rollback')
    search_fields = ('project', 'env', 'has_rollback')
