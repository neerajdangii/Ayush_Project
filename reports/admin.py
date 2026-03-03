from django.contrib import admin

from .models import Report


@admin.register(Report)
class ReportAdmin(admin.ModelAdmin):
    list_display = ("booking", "status", "manager_name", "incharge_name", "analysis_end_date", "created_at")
    list_filter = ("status",)
    search_fields = ("booking__sample_reg_no", "manager_name", "incharge_name")
