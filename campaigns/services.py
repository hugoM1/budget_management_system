"""
Services module for campaign business logic.
"""

from decimal import Decimal
from typing import Optional, List, Any
from django.utils import timezone
from django.db import transaction
import random
import logging

from .models import Campaign, Spend, Brand, DaypartingSchedule

logger = logging.getLogger(__name__)


def track_spend(campaign_id: int, amount: Decimal) -> None:
    """
    Track spend for a campaign.
    
    Args:
        campaign_id: The ID of the campaign
        amount: The amount to add to spend
    """
    try:
        with transaction.atomic():
            campaign = Campaign.objects.get(id=campaign_id)
            current_date = timezone.now().date()
            
            # Get or create spend record for today
            spend, created = Spend.objects.get_or_create(
                campaign=campaign,
                date=current_date,
                defaults={
                    'daily_spend': Decimal('0.00'),
                    'monthly_spend': Decimal('0.00')
                }
            )
            
            # Update spend amounts
            spend.add_spend(amount)
            
            # Check budget limits after adding spend
            check_budget_limits(campaign_id)
            
            logger.info(f"Tracked ${amount} spend for campaign {campaign_id}")
            
    except Campaign.DoesNotExist:
        logger.error(f"Campaign {campaign_id} not found")
        raise
    except Exception as e:
        logger.error(f"Error tracking spend for campaign {campaign_id}: {e}")
        raise


def check_budget_limits(campaign_id: int) -> None:
    """
    Check budget limits for a campaign and pause if necessary.
    
    Args:
        campaign_id: The ID of the campaign to check
    """
    try:
        campaign = Campaign.objects.get(id=campaign_id)
        spend = campaign.get_current_spend()
        
        if not spend:
            return  # No spend record, nothing to check
        
        # Check daily budget
        if spend.daily_spend >= campaign.daily_budget:
            if campaign.status == Campaign.Status.ACTIVE:
                campaign.pause(Campaign.PauseReason.DAILY_BUDGET_EXCEEDED)
                logger.info(f"Campaign {campaign_id} paused due to daily budget limit")
            return
        
        # Check monthly budget
        if spend.monthly_spend >= campaign.monthly_budget:
            if campaign.status == Campaign.Status.ACTIVE:
                campaign.pause(Campaign.PauseReason.MONTHLY_BUDGET_EXCEEDED)
                logger.info(f"Campaign {campaign_id} paused due to monthly budget limit")
            return
        
        # If campaign was paused due to budget, reactivate if within limits
        if (campaign.status == Campaign.Status.PAUSED and 
            campaign.pause_reason in [Campaign.PauseReason.DAILY_BUDGET_EXCEEDED, 
                                   Campaign.PauseReason.MONTHLY_BUDGET_EXCEEDED]):
            if campaign.is_budget_available():
                campaign.activate()
                logger.info(f"Campaign {campaign_id} reactivated after budget reset")
                
    except Campaign.DoesNotExist:
        logger.error(f"Campaign {campaign_id} not found")
        raise
    except Exception as e:
        logger.error(f"Error checking budget limits for campaign {campaign_id}: {e}")
        raise


def check_dayparting(campaign_id: int) -> bool:
    """
    Check if a campaign is within dayparting hours.
    
    Args:
        campaign_id: The ID of the campaign to check
        
    Returns:
        True if campaign is within dayparting hours, False otherwise
    """
    try:
        campaign = Campaign.objects.get(id=campaign_id)
        return campaign.is_within_dayparting_hours()
        
    except Campaign.DoesNotExist:
        logger.error(f"Campaign {campaign_id} not found")
        return False
    except Exception as e:
        logger.error(f"Error checking dayparting for campaign {campaign_id}: {e}")
        return False


def simulate_spend(campaign_id: int) -> None:
    """
    Simulate spend for an active campaign.
    
    Args:
        campaign_id: The ID of the campaign
    """
    try:
        campaign = Campaign.objects.get(id=campaign_id)
        
        if campaign.status != Campaign.Status.ACTIVE:
            return
        
        # Simulate spend based on campaign activity
        # In real implementation, this would come from actual ad serving data
        base_spend_rate = Decimal('0.01')  # $0.01 per minute
        random_factor = Decimal(str(random.uniform(0.5, 1.5)))
        spend_amount = base_spend_rate * random_factor
        
        track_spend(campaign_id, spend_amount)
        
    except Campaign.DoesNotExist:
        logger.error(f"Campaign {campaign_id} not found")
        raise
    except Exception as e:
        logger.error(f"Error simulating spend for campaign {campaign_id}: {e}")
        raise


def daily_reset() -> None:
    """Reset all daily spend records to zero."""
    try:
        with transaction.atomic():
            # Reset all daily spends to 0
            Spend.objects.all().update(daily_spend=Decimal('0.00'))
            
            # Reactivate campaigns that were paused due to daily budget
            paused_campaigns = Campaign.objects.filter(
                status=Campaign.Status.PAUSED,
                pause_reason=Campaign.PauseReason.DAILY_BUDGET_EXCEEDED
            )
            
            for campaign in paused_campaigns:
                if campaign.is_budget_available():
                    campaign.activate()
                    logger.info(f"Campaign {campaign.id} reactivated after daily reset")
            
            logger.info("Daily reset completed successfully")
            
    except Exception as e:
        logger.error(f"Error during daily reset: {e}")
        raise


def monthly_reset() -> None:
    """Reset all monthly spend records to zero."""
    try:
        current_date = timezone.now().date()
        
        # Only run on 1st of month
        if current_date.day != 1:
            logger.info("Monthly reset skipped - not the 1st of month")
            return
        
        with transaction.atomic():
            # Reset all monthly spends to 0
            Spend.objects.all().update(monthly_spend=Decimal('0.00'))
            
            # Reactivate campaigns that were paused due to monthly budget
            paused_campaigns = Campaign.objects.filter(
                status=Campaign.Status.PAUSED,
                pause_reason=Campaign.PauseReason.MONTHLY_BUDGET_EXCEEDED
            )
            
            for campaign in paused_campaigns:
                if campaign.is_budget_available():
                    campaign.activate()
                    logger.info(f"Campaign {campaign.id} reactivated after monthly reset")
            
            logger.info("Monthly reset completed successfully")
            
    except Exception as e:
        logger.error(f"Error during monthly reset: {e}")
        raise


def periodic_budget_check() -> None:
    """Periodic task to check budgets and dayparting for all campaigns."""
    try:
        current_time = timezone.now()
        logger.info(f"Starting periodic budget check at {current_time}")
        
        # Get all active campaigns
        active_campaigns = Campaign.objects.filter(status=Campaign.Status.ACTIVE)
        
        for campaign in active_campaigns:
            # Check dayparting
            if not check_dayparting(campaign.id):
                campaign.pause(Campaign.PauseReason.OUTSIDE_DAYPARTING_HOURS)
                logger.info(f"Campaign {campaign.id} paused due to dayparting")
                continue
            
            # Simulate spend for active campaigns
            simulate_spend(campaign.id)
        
        # Check for budget overruns
        for campaign in active_campaigns:
            check_budget_limits(campaign.id)
        
        logger.info("Periodic budget check completed")
        
    except Exception as e:
        logger.error(f"Error during periodic budget check: {e}")
        raise


def get_or_create_spend(campaign_id: int, date: Any) -> Spend:
    """
    Get or create a spend record for a campaign on a specific date.
    
    Args:
        campaign_id: The ID of the campaign
        date: The date for the spend record
        
    Returns:
        The spend record
    """
    try:
        campaign = Campaign.objects.get(id=campaign_id)
        spend, created = Spend.objects.get_or_create(
            campaign=campaign,
            date=date,
            defaults={
                'daily_spend': Decimal('0.00'),
                'monthly_spend': Decimal('0.00')
            }
        )
        
        if created:
            logger.info(f"Created new spend record for campaign {campaign_id} on {date}")
        
        return spend
        
    except Campaign.DoesNotExist:
        logger.error(f"Campaign {campaign_id} not found")
        raise
    except Exception as e:
        logger.error(f"Error getting/creating spend for campaign {campaign_id}: {e}")
        raise


def get_campaign_status_summary() -> dict:
    """
    Get a summary of campaign statuses.
    
    Returns:
        Dictionary with campaign status counts
    """
    try:
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
        summary['pause_reasons'] = {item['pause_reason']: item['count'] for item in pause_reasons}  # type: ignore
        
        return summary
        
    except Exception as e:
        logger.error(f"Error getting campaign status summary: {e}")
        return {} 