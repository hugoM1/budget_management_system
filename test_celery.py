#!/usr/bin/env python3
"""
Test script for Celery tasks in the Budget Management System.
"""

import os
import sys
import django
from decimal import Decimal

# Add the project directory to the Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Set up Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'budget_system.settings')
django.setup()

from campaigns.models import Brand, Campaign
from campaigns.tasks import (
    periodic_budget_check_task,
    daily_reset_task,
    monthly_reset_task,
    track_spend_task,
    check_budget_limits_task,
    simulate_spend_task,
    get_campaign_status_summary_task
)


def test_celery_tasks():
    """Test Celery tasks."""
    print("Testing Celery Tasks...")
    
    # Get or create test campaign
    brand, _ = Brand.objects.get_or_create(
        name="Test Brand",
        defaults={
            'daily_budget': Decimal('100.00'),
            'monthly_budget': Decimal('2000.00')
        }
    )
    
    campaign, _ = Campaign.objects.get_or_create(
        brand=brand,
        name="Test Campaign",
        defaults={
            'daily_budget': Decimal('50.00'),
            'monthly_budget': Decimal('1000.00'),
            'status': Campaign.Status.ACTIVE
        }
    )
    
    print(f"Testing with campaign: {campaign.name} (ID: {campaign.id})")
    
    # Test individual tasks
    print("\n1. Testing track_spend_task...")
    result = track_spend_task.delay(campaign.id, 15.50)
    print(f"Task ID: {result.id}")
    print(f"Status: {result.status}")
    
    print("\n2. Testing check_budget_limits_task...")
    result = check_budget_limits_task.delay(campaign.id)
    print(f"Task ID: {result.id}")
    print(f"Status: {result.status}")
    
    print("\n3. Testing simulate_spend_task...")
    result = simulate_spend_task.delay(campaign.id)
    print(f"Task ID: {result.id}")
    print(f"Status: {result.status}")
    
    print("\n4. Testing get_campaign_status_summary_task...")
    result = get_campaign_status_summary_task.delay()
    print(f"Task ID: {result.id}")
    print(f"Status: {result.status}")
    
    # Test periodic tasks (these would normally be scheduled)
    print("\n5. Testing periodic_budget_check_task...")
    result = periodic_budget_check_task.delay()
    print(f"Task ID: {result.id}")
    print(f"Status: {result.status}")
    
    print("\n6. Testing daily_reset_task...")
    result = daily_reset_task.delay()
    print(f"Task ID: {result.id}")
    print(f"Status: {result.status}")
    
    print("\n7. Testing monthly_reset_task...")
    result = monthly_reset_task.delay()
    print(f"Task ID: {result.id}")
    print(f"Status: {result.status}")
    
    print("\nCelery tasks test completed!")
    print("Note: Tasks are queued but need a Celery worker to execute them.")


if __name__ == "__main__":
    test_celery_tasks() 