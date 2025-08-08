"""
Django admin configuration for campaigns app.
"""

from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from django.utils.safestring import mark_safe
from typing import Any, List
from decimal import Decimal

from .models import Brand, Campaign, Spend, DaypartingSchedule


@admin.register(Brand)
class BrandAdmin(admin.ModelAdmin):
    """Admin interface for Brand model."""
    
    list_display: List[str] = [
        'name', 
        'daily_budget', 
        'monthly_budget', 
        'total_daily_spend', 
        'total_monthly_spend',
        'campaign_count',
        'created_at'
    ]
    list_filter: List[str] = ['created_at']
    search_fields: List[str] = ['name']
    readonly_fields: List[str] = ['created_at', 'updated_at']
    ordering: List[str] = ['name']
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('name', 'daily_budget', 'monthly_budget')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def total_daily_spend(self, obj: Brand) -> str:
        """Display total daily spend for the brand."""
        total = obj.get_total_daily_spend()
        return f"${total:.2f}"
    total_daily_spend.short_description = "Total Daily Spend"
    
    def total_monthly_spend(self, obj: Brand) -> str:
        """Display total monthly spend for the brand."""
        total = obj.get_total_monthly_spend()
        return f"${total:.2f}"
    total_monthly_spend.short_description = "Total Monthly Spend"
    
    def campaign_count(self, obj: Brand) -> int:
        """Display number of campaigns for the brand."""
        return obj.campaigns.count()
    campaign_count.short_description = "Campaigns"


@admin.register(Campaign)
class CampaignAdmin(admin.ModelAdmin):
    """Admin interface for Campaign model."""
    
    list_display: List[str] = [
        'name', 
        'brand', 
        'status', 
        'daily_budget', 
        'monthly_budget',
        'current_daily_spend',
        'current_monthly_spend',
        'budget_utilization',
        'pause_reason_display',
        'created_at'
    ]
    list_filter: List[str] = [
        'status', 
        'pause_reason', 
        'brand', 
        'created_at'
    ]
    search_fields: List[str] = ['name', 'brand__name']
    readonly_fields: List[str] = ['created_at', 'updated_at']
    ordering: List[str] = ['brand__name', 'name']
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('brand', 'name', 'status', 'pause_reason')
        }),
        ('Budget Settings', {
            'fields': ('daily_budget', 'monthly_budget')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    actions: List[str] = ['activate_campaigns', 'pause_campaigns', 'reset_budgets']
    
    def current_daily_spend(self, obj: Campaign) -> str:
        """Display current daily spend for the campaign."""
        spend = obj.get_current_spend()
        if spend:
            return f"${spend.daily_spend:.2f}"
        return "$0.00"
    current_daily_spend.short_description = "Current Daily Spend"
    
    def current_monthly_spend(self, obj: Campaign) -> str:
        """Display current monthly spend for the campaign."""
        spend = obj.get_current_spend()
        if spend:
            return f"${spend.monthly_spend:.2f}"
        return "$0.00"
    current_monthly_spend.short_description = "Current Monthly Spend"
    
    def budget_utilization(self, obj: Campaign) -> str:
        """Display budget utilization percentage."""
        spend = obj.get_current_spend()
        if not spend:
            return "0%"
        
        daily_utilization = (spend.daily_spend / obj.daily_budget) * 100
        monthly_utilization = (spend.monthly_spend / obj.monthly_budget) * 100
        
        # Return the higher utilization
        max_utilization = max(daily_utilization, monthly_utilization)
        max_utilization_float = float(max_utilization)
        
        if max_utilization_float >= 100:
            color = "red"
        elif max_utilization_float >= 80:
            color = "orange"
        else:
            color = "green"
        
        return mark_safe(f'<span style="color: {color};">{max_utilization_float:.1f}%</span>')
    budget_utilization.short_description = "Budget Utilization"
    
    def pause_reason_display(self, obj: Campaign) -> str:
        """Display pause reason with color coding."""
        if obj.pause_reason:
            return mark_safe(f'<span style="color: red;">{obj.get_pause_reason_display()}</span>')
        return mark_safe("-")
    pause_reason_display.short_description = "Pause Reason"
    
    def activate_campaigns(self, request: Any, queryset: Any) -> None:
        """Admin action to activate selected campaigns."""
        count = 0
        for campaign in queryset:
            campaign.activate()
            count += 1
        self.message_user(request, f"{count} campaigns activated successfully.")
    activate_campaigns.short_description = "Activate selected campaigns"
    
    def pause_campaigns(self, request: Any, queryset: Any) -> None:
        """Admin action to pause selected campaigns."""
        count = 0
        for campaign in queryset:
            campaign.pause(Campaign.PauseReason.MANUAL_PAUSE)
            count += 1
        self.message_user(request, f"{count} campaigns paused successfully.")
    pause_campaigns.short_description = "Pause selected campaigns"
    
    def reset_budgets(self, request: Any, queryset: Any) -> None:
        """Admin action to reset budgets for selected campaigns."""
        from .tasks import reset_all_budgets_task
        reset_all_budgets_task.delay()
        self.message_user(request, "Budget reset task queued successfully.")
    reset_budgets.short_description = "Reset all budgets"


@admin.register(Spend)
class SpendAdmin(admin.ModelAdmin):
    """Admin interface for Spend model."""
    
    list_display: List[str] = [
        'campaign', 
        'date', 
        'daily_spend', 
        'monthly_spend',
        'daily_budget_utilization',
        'monthly_budget_utilization',
        'created_at'
    ]
    list_filter: List[str] = ['date', 'campaign__brand', 'campaign', 'created_at']
    search_fields: List[str] = ['campaign__name', 'campaign__brand__name']
    readonly_fields: List[str] = ['created_at', 'updated_at']
    ordering: List[str] = ['-date', 'campaign__name']
    
    fieldsets = (
        ('Spend Information', {
            'fields': ('campaign', 'date', 'daily_spend', 'monthly_spend')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def daily_budget_utilization(self, obj: Spend) -> str:
        """Display daily budget utilization percentage."""
        if obj.campaign.daily_budget > 0:
            utilization = (obj.daily_spend / obj.campaign.daily_budget) * 100
            utilization_float = float(utilization)
            color = "red" if utilization_float >= 100 else "green"
            return mark_safe(f'<span style="color: {color};">{utilization_float:.1f}%</span>')
        return "0%"
    daily_budget_utilization.short_description = "Daily Budget %"
    
    def monthly_budget_utilization(self, obj: Spend) -> str:
        """Display monthly budget utilization percentage."""
        if obj.campaign.monthly_budget > 0:
            utilization = (obj.monthly_spend / obj.campaign.monthly_budget) * 100
            utilization_float = float(utilization)
            color = "red" if utilization_float >= 100 else "green"
            return mark_safe(f'<span style="color: {color};">{utilization_float:.1f}%</span>')
        return "0%"
    monthly_budget_utilization.short_description = "Monthly Budget %"


@admin.register(DaypartingSchedule)
class DaypartingScheduleAdmin(admin.ModelAdmin):
    """Admin interface for DaypartingSchedule model."""
    
    list_display: List[str] = [
        'campaign', 
        'day_of_week', 
        'start_time', 
        'end_time', 
        'is_active',
        'duration_hours',
        'created_at'
    ]
    list_filter: List[str] = [
        'day_of_week', 
        'is_active', 
        'campaign__brand', 
        'created_at'
    ]
    search_fields: List[str] = ['campaign__name', 'campaign__brand__name']
    readonly_fields: List[str] = ['created_at', 'updated_at']
    ordering: List[str] = ['day_of_week', 'start_time']
    
    fieldsets = (
        ('Schedule Information', {
            'fields': ('campaign', 'day_of_week', 'start_time', 'end_time', 'is_active')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def duration_hours(self, obj: DaypartingSchedule) -> str:
        """Display duration in hours."""
        from datetime import datetime, timedelta
        
        start = datetime.combine(datetime.today(), obj.start_time)
        end = datetime.combine(datetime.today(), obj.end_time)
        
        if end < start:
            end += timedelta(days=1)
        
        duration = end - start
        hours = duration.total_seconds() / 3600
        
        return f"{hours:.1f} hours"
    duration_hours.short_description = "Duration"


# Custom admin site configuration
admin.site.site_header = "Budget Management System"
admin.site.site_title = "Budget Management Admin"
admin.site.index_title = "Welcome to Budget Management System"
