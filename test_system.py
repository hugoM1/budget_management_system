#!/usr/bin/env python3
"""
Test script for the Budget Management System.
"""

import os
import sys
import django
from decimal import Decimal
from datetime import time

# Add the project directory to the Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Set up Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'budget_system.settings')
django.setup()

from campaigns.models import Brand, Campaign, Spend, DaypartingSchedule
from campaigns.services import track_spend, check_budget_limits, simulate_spend


def test_system() -> None:
    """Test the budget management system."""
    print("Testing Budget Management System...")
    
    # Create a test brand
    brand, created = Brand.objects.get_or_create(
        name="Test Brand",
        defaults={
            'daily_budget': Decimal('100.00'),
            'monthly_budget': Decimal('2000.00')
        }
    )
    print(f"Brand: {brand.name} (Daily: ${brand.daily_budget}, Monthly: ${brand.monthly_budget})")
    
    # Create a test campaign
    campaign, created = Campaign.objects.get_or_create(
        brand=brand,
        name="Test Campaign",
        defaults={
            'daily_budget': Decimal('50.00'),
            'monthly_budget': Decimal('1000.00'),
            'status': Campaign.Status.ACTIVE
        }
    )
    print(f"Campaign: {campaign.name} (Daily: ${campaign.daily_budget}, Monthly: ${campaign.monthly_budget})")
    
    # Create a dayparting schedule (Monday-Friday, 9 AM - 5 PM)
    schedule, created = DaypartingSchedule.objects.get_or_create(
        campaign=campaign,
        day_of_week=0,  # Monday
        defaults={
            'start_time': time(9, 0),  # 9 AM
            'end_time': time(17, 0),   # 5 PM
            'is_active': True
        }
    )
    print(f"Dayparting Schedule: {schedule}")
    
    # Test spend tracking
    print("\nTesting spend tracking...")
    track_spend(campaign.id, Decimal('10.00'))
    
    # Check current spend
    spend = campaign.get_current_spend()
    if spend:
        print(f"Current daily spend: ${spend.daily_spend}")
        print(f"Current monthly spend: ${spend.monthly_spend}")
    
    # Test budget limits
    print("\nTesting budget limits...")
    check_budget_limits(campaign.id)
    print(f"Campaign status: {campaign.status}")
    if campaign.pause_reason:
        print(f"Pause reason: {campaign.pause_reason}")
    
    # Test spend simulation
    print("\nTesting spend simulation...")
    simulate_spend(campaign.id)
    
    # Check updated spend
    spend = campaign.get_current_spend()
    if spend:
        print(f"Updated daily spend: ${spend.daily_spend}")
        print(f"Updated monthly spend: ${spend.monthly_spend}")
    
    # Test dayparting
    print("\nTesting dayparting...")
    is_within_hours = campaign.is_within_dayparting_hours()
    print(f"Within dayparting hours: {is_within_hours}")
    
    print("\nSystem test completed successfully!")


if __name__ == "__main__":
    test_system()