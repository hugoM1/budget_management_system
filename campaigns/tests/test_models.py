from decimal import Decimal
from datetime import time
from django.core.exceptions import ValidationError
from django.test import TestCase
from django.utils import timezone

from campaigns.models import Brand, Campaign, Spend, DaypartingSchedule


class ModelTests(TestCase):
    def setUp(self) -> None:
        self.brand = Brand.objects.create(
            name="BrandA", daily_budget=Decimal("100.00"), monthly_budget=Decimal("1000.00")
        )
        self.campaign = Campaign.objects.create(
            brand=self.brand,
            name="Camp1",
            status=Campaign.Status.ACTIVE,
            daily_budget=Decimal("50.00"),
            monthly_budget=Decimal("500.00"),
        )

    def test_brand_total_spend_aggregations(self) -> None:
        today = timezone.now().date()
        Spend.objects.create(
            campaign=self.campaign, date=today, daily_spend=Decimal("10.00"), monthly_spend=Decimal("100.00")
        )
        self.assertEqual(self.brand.get_total_daily_spend(), Decimal("10.00"))
        self.assertEqual(self.brand.get_total_monthly_spend(), Decimal("100.00"))

    def test_campaign_get_current_spend(self) -> None:
        today = timezone.now().date()
        self.assertIsNone(self.campaign.get_current_spend())
        s = Spend.objects.create(
            campaign=self.campaign, date=today, daily_spend=Decimal("5.00"), monthly_spend=Decimal("5.00")
        )
        self.assertEqual(self.campaign.get_current_spend().id, s.id)

    def test_campaign_is_budget_available(self) -> None:
        today = timezone.now().date()
        Spend.objects.create(
            campaign=self.campaign, date=today, daily_spend=Decimal("49.99"), monthly_spend=Decimal("499.99")
        )
        self.assertTrue(self.campaign.is_budget_available())
        # At boundary - equals budget should be unavailable per >= checks
        Spend.objects.filter(campaign=self.campaign, date=today).update(
            daily_spend=Decimal("50.00"), monthly_spend=Decimal("500.00")
        )
        self.assertFalse(self.campaign.is_budget_available())

    def test_dayparting_schedule_validation(self) -> None:
        # Invalid: start >= end
        sched = DaypartingSchedule(
            campaign=self.campaign,
            day_of_week=0,
            start_time=time(10, 0),
            end_time=time(9, 0),
        )
        with self.assertRaises(ValidationError):
            sched.full_clean()
        # Overlap detection
        DaypartingSchedule.objects.create(
            campaign=self.campaign, day_of_week=1, start_time=time(9, 0), end_time=time(12, 0)
        )
        overlap = DaypartingSchedule(
            campaign=self.campaign, day_of_week=1, start_time=time(11, 0), end_time=time(13, 0)
        )
        with self.assertRaises(ValidationError):
            overlap.full_clean()

    def test_spend_methods(self) -> None:
        today = timezone.now().date()
        s = Spend.objects.create(
            campaign=self.campaign, date=today, daily_spend=Decimal("1.00"), monthly_spend=Decimal("2.00")
        )
        s.add_spend(Decimal("3.00"))
        self.assertEqual(s.daily_spend, Decimal("4.00"))
        self.assertEqual(s.monthly_spend, Decimal("5.00"))
        s.reset_daily_spend()
        self.assertEqual(s.daily_spend, Decimal("0.00"))
        s.reset_monthly_spend()
        self.assertEqual(s.monthly_spend, Decimal("0.00"))
