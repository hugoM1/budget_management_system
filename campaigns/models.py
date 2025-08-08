"""
Models for the campaigns app.
"""

from django.db import models
from django.core.validators import MinValueValidator
from django.utils import timezone
from decimal import Decimal
from typing import Optional, List
import logging

logger = logging.getLogger(__name__)


class Brand(models.Model):
    """Model representing an advertising brand/client."""
    
    name = models.CharField(max_length=255, unique=True)
    daily_budget = models.DecimalField(
        max_digits=10, 
        decimal_places=2, 
        validators=[MinValueValidator(Decimal('0.01'))]
    )
    monthly_budget = models.DecimalField(
        max_digits=10, 
        decimal_places=2, 
        validators=[MinValueValidator(Decimal('0.01'))]
    )
    created_at: models.DateTimeField = models.DateTimeField(auto_now_add=True)
    updated_at: models.DateTimeField = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'brands'
        ordering = ['name']

    def __str__(self) -> str:
        return self.name

    def get_total_daily_spend(self) -> Decimal:
        """Get total daily spend across all campaigns for this brand."""
        total: Decimal = Decimal('0.00')
        for campaign in self.campaigns.all():
            spend = campaign.get_current_spend()
            if spend:
                total += spend.daily_spend
        return total

    def get_total_monthly_spend(self) -> Decimal:
        """Get total monthly spend across all campaigns for this brand."""
        total: Decimal = Decimal('0.00')
        for campaign in self.campaigns.all():
            spend = campaign.get_current_spend()
            if spend:
                total += spend.monthly_spend
        return total


class Campaign(models.Model):
    """Model representing an advertising campaign."""
    
    class Status(models.TextChoices):
        ACTIVE = 'ACTIVE', 'Active'
        INACTIVE = 'INACTIVE', 'Inactive'
        PAUSED = 'PAUSED', 'Paused'

    class PauseReason(models.TextChoices):
        DAILY_BUDGET_EXCEEDED = 'DAILY_BUDGET_EXCEEDED', 'Daily Budget Exceeded'
        MONTHLY_BUDGET_EXCEEDED = 'MONTHLY_BUDGET_EXCEEDED', 'Monthly Budget Exceeded'
        OUTSIDE_DAYPARTING_HOURS = 'OUTSIDE_DAYPARTING_HOURS', 'Outside Dayparting Hours'
        MANUAL_PAUSE = 'MANUAL_PAUSE', 'Manually Paused'

    brand = models.ForeignKey(
        Brand, 
        on_delete=models.CASCADE, 
        related_name='campaigns'
    )
    name = models.CharField(max_length=255)
    status = models.CharField(
        max_length=20, 
        choices=Status.choices, 
        default=Status.INACTIVE
    )
    daily_budget = models.DecimalField(
        max_digits=10, 
        decimal_places=2, 
        validators=[MinValueValidator(Decimal('0.01'))]
    )
    monthly_budget = models.DecimalField(
        max_digits=10, 
        decimal_places=2, 
        validators=[MinValueValidator(Decimal('0.01'))]
    )
    pause_reason = models.CharField(
        max_length=50, 
        choices=PauseReason.choices, 
        null=True, 
        blank=True
    )
    created_at: models.DateTimeField = models.DateTimeField(auto_now_add=True)
    updated_at: models.DateTimeField = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'campaigns'
        ordering = ['brand__name', 'name']
        unique_together = ['brand', 'name']

    def __str__(self) -> str:
        return f"{self.brand.name} - {self.name}"

    def get_current_spend(self) -> Optional['Spend']:
        """Get the current spend record for today."""
        today = timezone.now().date()
        return self.spends.filter(date=today).first()

    def is_budget_available(self) -> bool:
        """Check if budget is available for this campaign."""
        spend = self.get_current_spend()
        if not spend:
            return True
        
        daily_available = spend.daily_spend < self.daily_budget
        monthly_available = spend.monthly_spend < self.monthly_budget
        
        return daily_available and monthly_available

    def activate(self) -> None:
        """Activate the campaign."""
        self.status = self.Status.ACTIVE
        self.pause_reason = None
        self.save()
        logger.info(f"Campaign {self.id} activated")

    def pause(self, reason: str) -> None:
        """Pause the campaign with a reason."""
        self.status = self.Status.PAUSED
        self.pause_reason = reason
        self.save()
        logger.info(f"Campaign {self.id} paused: {reason}")

    def is_within_dayparting_hours(self) -> bool:
        """Check if campaign is within dayparting hours."""
        now = timezone.now()
        day_of_week = now.weekday()
        current_time = now.time()
        
        # Get active dayparting schedules for today
        schedules = self.dayparting_schedules.filter(
            day_of_week=day_of_week,
            is_active=True
        )
        
        if not schedules.exists():
            return True  # No restrictions
        
        for schedule in schedules:
            if schedule.start_time <= current_time <= schedule.end_time:
                return True
        
        return False


class Spend(models.Model):
    """Model representing daily and monthly spend for campaigns."""
    
    campaign = models.ForeignKey(
        Campaign, 
        on_delete=models.CASCADE, 
        related_name='spends'
    )
    date = models.DateField()
    daily_spend = models.DecimalField(
        max_digits=10, 
        decimal_places=2, 
        default=Decimal('0.00')
    )
    monthly_spend = models.DecimalField(
        max_digits=10, 
        decimal_places=2, 
        default=Decimal('0.00')
    )
    created_at: models.DateTimeField = models.DateTimeField(auto_now_add=True)
    updated_at: models.DateTimeField = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'spends'
        unique_together = ['campaign', 'date']
        ordering = ['-date']

    def __str__(self) -> str:
        return f"{self.campaign.name} - {self.date} - ${self.daily_spend}"

    def add_spend(self, amount: Decimal) -> None:
        """Add spend amount to the record."""
        self.daily_spend += amount
        self.monthly_spend += amount
        self.save()
        logger.info(f"Added ${amount} spend to campaign {self.campaign.id}")

    def reset_daily_spend(self) -> None:
        """Reset daily spend to zero."""
        self.daily_spend = Decimal('0.00')
        self.save()
        logger.info(f"Reset daily spend for campaign {self.campaign.id}")

    def reset_monthly_spend(self) -> None:
        """Reset monthly spend to zero."""
        self.monthly_spend = Decimal('0.00')
        self.save()
        logger.info(f"Reset monthly spend for campaign {self.campaign.id}")


class DaypartingSchedule(models.Model):
    """Model representing dayparting schedules for campaigns."""
    
    DAYS_OF_WEEK = [
        (0, 'Monday'),
        (1, 'Tuesday'),
        (2, 'Wednesday'),
        (3, 'Thursday'),
        (4, 'Friday'),
        (5, 'Saturday'),
        (6, 'Sunday'),
    ]

    campaign = models.ForeignKey(
        Campaign, 
        on_delete=models.CASCADE, 
        related_name='dayparting_schedules'
    )
    day_of_week = models.IntegerField(choices=DAYS_OF_WEEK)
    start_time = models.TimeField()
    end_time = models.TimeField()
    is_active = models.BooleanField(default=True)
    created_at: models.DateTimeField = models.DateTimeField(auto_now_add=True)
    updated_at: models.DateTimeField = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'dayparting_schedules'
        ordering = ['day_of_week', 'start_time']

    def __str__(self) -> str:
        return f"{self.campaign.name} - {self.get_day_of_week_display()} {self.start_time}-{self.end_time}"

    def clean(self) -> None:
        """Validate the model."""
        from django.core.exceptions import ValidationError
        
        if self.start_time >= self.end_time:
            raise ValidationError("Start time must be before end time")
        
        # Check for overlapping schedules
        overlapping = DaypartingSchedule.objects.filter(
            campaign=self.campaign,
            day_of_week=self.day_of_week,
            is_active=True
        ).exclude(id=self.id)
        
        for schedule in overlapping:
            if (self.start_time < schedule.end_time and 
                self.end_time > schedule.start_time):
                raise ValidationError("Schedule overlaps with existing schedule")
