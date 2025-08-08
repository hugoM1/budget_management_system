"""
Celery tasks for campaign management.
"""

from celery import shared_task
from typing import Any
import logging

from .services import (
    periodic_budget_check,
    daily_reset,
    monthly_reset,
    track_spend,
    check_budget_limits,
    check_dayparting,
    simulate_spend
)
from .models import Campaign, Spend

logger = logging.getLogger(__name__)


@shared_task(bind=True)
def periodic_budget_check_task(self: Any) -> str:
    """
    Periodic task to check budgets and dayparting for all campaigns.
    
    Returns:
        Status message
    """
    try:
        logger.info("Starting periodic budget check task")
        periodic_budget_check()
        return "Periodic budget check completed successfully"
    except Exception as e:
        logger.error(f"Error in periodic budget check task: {e}")
        raise


@shared_task(bind=True)
def daily_reset_task(self: Any) -> str:
    """
    Daily reset task to reset all daily spend records.
    
    Returns:
        Status message
    """
    try:
        logger.info("Starting daily reset task")
        daily_reset()
        return "Daily reset completed successfully"
    except Exception as e:
        logger.error(f"Error in daily reset task: {e}")
        raise


@shared_task(bind=True)
def monthly_reset_task(self: Any) -> str:
    """
    Monthly reset task to reset all monthly spend records.
    
    Returns:
        Status message
    """
    try:
        logger.info("Starting monthly reset task")
        monthly_reset()
        return "Monthly reset completed successfully"
    except Exception as e:
        logger.error(f"Error in monthly reset task: {e}")
        raise


@shared_task(bind=True)
def track_spend_task(self: Any, campaign_id: int, amount: float) -> str:
    """
    Task to track spend for a campaign.
    
    Args:
        campaign_id: The ID of the campaign
        amount: The amount to add to spend
        
    Returns:
        Status message
    """
    try:
        from decimal import Decimal
        logger.info(f"Starting track spend task for campaign {campaign_id}")
        track_spend(campaign_id, Decimal(str(amount)))
        return f"Spend tracking completed for campaign {campaign_id}"
    except Exception as e:
        logger.error(f"Error in track spend task for campaign {campaign_id}: {e}")
        raise


@shared_task(bind=True)
def check_budget_limits_task(self: Any, campaign_id: int) -> str:
    """
    Task to check budget limits for a campaign.
    
    Args:
        campaign_id: The ID of the campaign to check
        
    Returns:
        Status message
    """
    try:
        logger.info(f"Starting budget limits check task for campaign {campaign_id}")
        check_budget_limits(campaign_id)
        return f"Budget limits check completed for campaign {campaign_id}"
    except Exception as e:
        logger.error(f"Error in budget limits check task for campaign {campaign_id}: {e}")
        raise


@shared_task(bind=True)
def check_dayparting_task(self: Any, campaign_id: int) -> str:
    """
    Task to check dayparting for a campaign.
    
    Args:
        campaign_id: The ID of the campaign to check
        
    Returns:
        Status message
    """
    try:
        logger.info(f"Starting dayparting check task for campaign {campaign_id}")
        is_within_hours = check_dayparting(campaign_id)
        return f"Dayparting check completed for campaign {campaign_id}: {'within hours' if is_within_hours else 'outside hours'}"
    except Exception as e:
        logger.error(f"Error in dayparting check task for campaign {campaign_id}: {e}")
        raise


@shared_task(bind=True)
def simulate_spend_task(self: Any, campaign_id: int) -> str:
    """
    Task to simulate spend for a campaign.
    
    Args:
        campaign_id: The ID of the campaign
        
    Returns:
        Status message
    """
    try:
        logger.info(f"Starting spend simulation task for campaign {campaign_id}")
        simulate_spend(campaign_id)
        return f"Spend simulation completed for campaign {campaign_id}"
    except Exception as e:
        logger.error(f"Error in spend simulation task for campaign {campaign_id}: {e}")
        raise


@shared_task(bind=True)
def reset_all_budgets_task(self: Any) -> str:
    """
    Task to reset all budgets (for testing purposes).
    
    Returns:
        Status message
    """
    try:
        logger.info("Starting reset all budgets task")
        
        # Reset all daily and monthly spends
        from decimal import Decimal
        Spend.objects.all().update(
            daily_spend=Decimal('0.00'),
            monthly_spend=Decimal('0.00')
        )
        
        # Reactivate all paused campaigns
        paused_campaigns = Campaign.objects.filter(status=Campaign.Status.PAUSED)
        for campaign in paused_campaigns:
            campaign.activate()
        
        logger.info("Reset all budgets completed successfully")
        return "Reset all budgets completed successfully"
    except Exception as e:
        logger.error(f"Error in reset all budgets task: {e}")
        raise


@shared_task(bind=True)
def get_campaign_status_summary_task(self: Any) -> dict:
    """
    Task to get campaign status summary.
    
    Returns:
        Dictionary with campaign status summary
    """
    try:
        logger.info("Starting campaign status summary task")
        
        summary = {
            'active': Campaign.objects.filter(status=Campaign.Status.ACTIVE).count(),
            'inactive': Campaign.objects.filter(status=Campaign.Status.INACTIVE).count(),
            'paused': Campaign.objects.filter(status=Campaign.Status.PAUSED).count(),
            'total': Campaign.objects.count(),
        }
        
        # Add pause reason breakdown
        from django.db import models
        pause_reasons = Campaign.objects.filter(status=Campaign.Status.PAUSED).values('pause_reason').annotate(
            count=models.Count('id')
        )
        summary['pause_reasons'] = {item['pause_reason']: item['count'] for item in pause_reasons}
        
        logger.info(f"Campaign status summary: {summary}")
        return summary
        
    except Exception as e:
        logger.error(f"Error in campaign status summary task: {e}")
        return {}


@shared_task(bind=True)
def debug_task(self: Any) -> str:
    """
    Debug task to test Celery setup.
    
    Returns:
        Debug message
    """
    logger.info(f"Debug task executed: {self.request.id}")
    return f"Debug task completed: {self.request.id}" 