"""
Management command to create sample data for testing the budget management system.
"""

from django.core.management.base import BaseCommand
from django.utils import timezone
from decimal import Decimal
from campaigns.models import Brand, Campaign, Spend, DaypartingSchedule
from datetime import time


class Command(BaseCommand):
    help = 'Create sample data for testing the budget management system'

    def handle(self, *args, **options):
        self.stdout.write('Creating sample data...')
        
        # Create sample brands
        brands = []
        brand_data = [
            {
                'name': 'TechCorp',
                'daily_budget': Decimal('1000.00'),
                'monthly_budget': Decimal('25000.00')
            },
            {
                'name': 'FashionForward',
                'daily_budget': Decimal('500.00'),
                'monthly_budget': Decimal('12000.00')
            },
            {
                'name': 'FoodDelivery',
                'daily_budget': Decimal('750.00'),
                'monthly_budget': Decimal('18000.00')
            }
        ]
        
        for data in brand_data:
            brand, created = Brand.objects.get_or_create(
                name=data['name'],
                defaults=data
            )
            brands.append(brand)
            if created:
                self.stdout.write(f'✅ Created brand: {brand.name}')
            else:
                self.stdout.write(f'⚠️  Brand already exists: {brand.name}')
        
        # Create sample campaigns
        campaigns = []
        campaign_data = [
            {
                'brand': brands[0],  # TechCorp
                'name': 'Summer Tech Sale',
                'daily_budget': Decimal('400.00'),
                'monthly_budget': Decimal('10000.00'),
                'status': Campaign.Status.ACTIVE
            },
            {
                'brand': brands[0],  # TechCorp
                'name': 'Back to School',
                'daily_budget': Decimal('300.00'),
                'monthly_budget': Decimal('8000.00'),
                'status': Campaign.Status.ACTIVE
            },
            {
                'brand': brands[1],  # FashionForward
                'name': 'Fall Collection',
                'daily_budget': Decimal('250.00'),
                'monthly_budget': Decimal('6000.00'),
                'status': Campaign.Status.ACTIVE
            },
            {
                'brand': brands[1],  # FashionForward
                'name': 'Holiday Special',
                'daily_budget': Decimal('200.00'),
                'monthly_budget': Decimal('5000.00'),
                'status': Campaign.Status.INACTIVE
            },
            {
                'brand': brands[2],  # FoodDelivery
                'name': 'Weekend Promo',
                'daily_budget': Decimal('350.00'),
                'monthly_budget': Decimal('9000.00'),
                'status': Campaign.Status.ACTIVE
            }
        ]
        
        for data in campaign_data:
            campaign, created = Campaign.objects.get_or_create(
                brand=data['brand'],
                name=data['name'],
                defaults=data
            )
            campaigns.append(campaign)
            if created:
                self.stdout.write(f'✅ Created campaign: {campaign.name}')
            else:
                self.stdout.write(f'⚠️  Campaign already exists: {campaign.name}')
        
        # Create sample spend data
        today = timezone.now().date()
        spend_data = [
            {
                'campaign': campaigns[0],  # Summer Tech Sale
                'daily_spend': Decimal('150.25'),
                'monthly_spend': Decimal('3200.50')
            },
            {
                'campaign': campaigns[1],  # Back to School
                'daily_spend': Decimal('89.75'),
                'monthly_spend': Decimal('2100.25')
            },
            {
                'campaign': campaigns[2],  # Fall Collection
                'daily_spend': Decimal('125.00'),
                'monthly_spend': Decimal('2800.00')
            },
            {
                'campaign': campaigns[4],  # Weekend Promo
                'daily_spend': Decimal('200.50'),
                'monthly_spend': Decimal('4500.75')
            }
        ]
        
        for data in spend_data:
            spend, created = Spend.objects.get_or_create(
                campaign=data['campaign'],
                date=today,
                defaults=data
            )
            if created:
                self.stdout.write(f'✅ Created spend record for: {spend.campaign.name}')
            else:
                self.stdout.write(f'⚠️  Spend record already exists for: {spend.campaign.name}')
        
        # Create sample dayparting schedules
        dayparting_data = [
            {
                'campaign': campaigns[0],  # Summer Tech Sale
                'day_of_week': 0,  # Monday
                'start_time': time(9, 0),  # 9:00 AM
                'end_time': time(17, 0),   # 5:00 PM
            },
            {
                'campaign': campaigns[0],  # Summer Tech Sale
                'day_of_week': 1,  # Tuesday
                'start_time': time(9, 0),
                'end_time': time(17, 0),
            },
            {
                'campaign': campaigns[2],  # Fall Collection
                'day_of_week': 5,  # Saturday
                'start_time': time(10, 0),  # 10:00 AM
                'end_time': time(18, 0),   # 6:00 PM
            },
            {
                'campaign': campaigns[4],  # Weekend Promo
                'day_of_week': 5,  # Saturday
                'start_time': time(11, 0),  # 11:00 AM
                'end_time': time(20, 0),   # 8:00 PM
            },
            {
                'campaign': campaigns[4],  # Weekend Promo
                'day_of_week': 6,  # Sunday
                'start_time': time(12, 0),  # 12:00 PM
                'end_time': time(19, 0),   # 7:00 PM
            }
        ]
        
        for data in dayparting_data:
            schedule, created = DaypartingSchedule.objects.get_or_create(
                campaign=data['campaign'],
                day_of_week=data['day_of_week'],
                start_time=data['start_time'],
                end_time=data['end_time'],
                defaults={'is_active': True}
            )
            if created:
                self.stdout.write(f'✅ Created dayparting schedule for: {schedule.campaign.name}')
            else:
                self.stdout.write(f'⚠️  Dayparting schedule already exists for: {schedule.campaign.name}')
        
        self.stdout.write(
            self.style.SUCCESS(
                f'\n✅ Sample data created successfully!\n'
                f'• {len(brands)} brands\n'
                f'• {len(campaigns)} campaigns\n'
                f'• {len(spend_data)} spend records\n'
                f'• {len(dayparting_data)} dayparting schedules\n\n'
                f'You can now test the budget management system in the admin interface!'
            )
        ) 