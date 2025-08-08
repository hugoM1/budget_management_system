"""
Django management command to reset all budgets.
"""

from django.core.management.base import BaseCommand
from django.utils import timezone
from decimal import Decimal
from typing import Any
import logging

from campaigns.models import Spend, Campaign
from campaigns.tasks import reset_all_budgets_task

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    """Management command to reset all budgets."""
    
    help: str = "Reset all daily and monthly spend records to zero"
    
    def add_arguments(self, parser: Any) -> None:
        """Add command arguments."""
        parser.add_argument(
            '--force',
            action='store_true',
            help='Force reset even if not the 1st of month',
        )
        parser.add_argument(
            '--async',
            action='store_true',
            help='Run reset asynchronously using Celery',
        )
    
    def handle(self, *args: Any, **options: Any) -> None:
        """Handle the command execution."""
        force = options.get('force', False)
        async_mode = options.get('async', False)
        
        current_date = timezone.now().date()
        
        if not force and current_date.day != 1:
            self.stdout.write(
                self.style.WARNING(
                    f"Today is {current_date.day}, not the 1st of month. "
                    "Use --force to reset anyway."
                )
            )
            return
        
        if async_mode:
            # Queue the task for asynchronous execution
            task = reset_all_budgets_task.delay()
            self.stdout.write(
                self.style.SUCCESS(
                    f"Budget reset task queued with ID: {task.id}"
                )
            )
        else:
            # Execute synchronously
            try:
                from django.db import transaction
                with transaction.atomic():
                    # Reset all daily and monthly spends
                    updated_count = Spend.objects.all().update(
                        daily_spend=Decimal('0.00'),
                        monthly_spend=Decimal('0.00')
                    )
                    
                    # Reactivate all paused campaigns
                    paused_campaigns = Campaign.objects.filter(
                        status=Campaign.Status.PAUSED
                    )
                    reactivated_count = 0
                    
                    for campaign in paused_campaigns:
                        campaign.activate()
                        reactivated_count += 1
                    
                    self.stdout.write(
                        self.style.SUCCESS(
                            f"Successfully reset {updated_count} spend records "
                            f"and reactivated {reactivated_count} campaigns."
                        )
                    )
                    
                    logger.info(
                        f"Budget reset completed: {updated_count} records reset, "
                        f"{reactivated_count} campaigns reactivated"
                    )
                    
            except Exception as e:
                self.stdout.write(
                    self.style.ERROR(f"Error during budget reset: {e}")
                )
                logger.error(f"Error during budget reset: {e}")
                raise 