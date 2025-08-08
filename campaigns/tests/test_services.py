from decimal import Decimal
from datetime import time
from django.test import TestCase
from django.utils import timezone

from campaigns.models import Brand, Campaign, Spend, DaypartingSchedule
from campaigns.services import (
    track_spend,
    check_budget_limits,
    check_dayparting,
    simulate_spend,
    daily_reset,
    monthly_reset,
    get_or_create_spend,
    get_campaign_status_summary,
)


class ServicesTests(TestCase):
    def setUp(self) -> None:
        self.brand = Brand.objects.create(
            name="UnitTest Brand", daily_budget=Decimal("100.00"), monthly_budget=Decimal("2000.00")
        )
        self.campaign = Campaign.objects.create(
            brand=self.brand,
            name="UnitTest Campaign",
            status=Campaign.Status.ACTIVE,
            daily_budget=Decimal("50.00"),
            monthly_budget=Decimal("1000.00"),
        )
        DaypartingSchedule.objects.create(
            campaign=self.campaign, day_of_week=timezone.now().weekday(), start_time=time(0, 0), end_time=time(23, 59)
        )

    def test_track_spend_creates_and_updates_spend(self) -> None:
        today = timezone.now().date()
        self.assertFalse(Spend.objects.filter(campaign=self.campaign, date=today).exists())
        track_spend(self.campaign.id, Decimal("10.00"))
        spend = Spend.objects.get(campaign=self.campaign, date=today)
        self.assertEqual(spend.daily_spend, Decimal("10.00"))
        self.assertEqual(spend.monthly_spend, Decimal("10.00"))

    def test_check_budget_limits_pauses_on_daily(self) -> None:
        today = timezone.now().date()
        spend = Spend.objects.create(
            campaign=self.campaign, date=today, daily_spend=Decimal("50.00"), monthly_spend=Decimal("50.00")
        )
        check_budget_limits(self.campaign.id)
        self.campaign.refresh_from_db()
        self.assertEqual(self.campaign.status, Campaign.Status.PAUSED)
        self.assertEqual(self.campaign.pause_reason, Campaign.PauseReason.DAILY_BUDGET_EXCEEDED)

    def test_check_budget_limits_pauses_on_monthly(self) -> None:
        self.campaign.daily_budget = Decimal("1000.00")
        self.campaign.save()
        today = timezone.now().date()
        Spend.objects.create(
            campaign=self.campaign, date=today, daily_spend=Decimal("10.00"), monthly_spend=Decimal("1000.00")
        )
        check_budget_limits(self.campaign.id)
        self.campaign.refresh_from_db()
        self.assertEqual(self.campaign.status, Campaign.Status.PAUSED)
        self.assertEqual(self.campaign.pause_reason, Campaign.PauseReason.MONTHLY_BUDGET_EXCEEDED)

    def test_check_dayparting_true_when_within(self) -> None:
        self.assertTrue(check_dayparting(self.campaign.id))

    def test_simulate_spend_adds_amount_for_active(self) -> None:
        today = timezone.now().date()
        simulate_spend(self.campaign.id)
        self.assertTrue(Spend.objects.filter(campaign=self.campaign, date=today).exists())

    def test_daily_reset_resets_and_reactivates(self) -> None:
        today = timezone.now().date()
        Spend.objects.create(
            campaign=self.campaign, date=today, daily_spend=Decimal("25.00"), monthly_spend=Decimal("25.00")
        )
        self.campaign.pause(Campaign.PauseReason.DAILY_BUDGET_EXCEEDED)
        daily_reset()
        spend = Spend.objects.get(campaign=self.campaign, date=today)
        self.campaign.refresh_from_db()
        self.assertEqual(spend.daily_spend, Decimal("0.00"))
        self.assertEqual(self.campaign.status, Campaign.Status.ACTIVE)

    def test_get_or_create_spend(self) -> None:
        today = timezone.now().date()
        spend = get_or_create_spend(self.campaign.id, today)
        self.assertEqual(spend.daily_spend, Decimal("0.00"))
        again = get_or_create_spend(self.campaign.id, today)
        self.assertEqual(spend.id, again.id)

    def test_get_campaign_status_summary(self) -> None:
        summary = get_campaign_status_summary()
        self.assertIn("active", summary)
        self.assertIn("inactive", summary)
        self.assertIn("paused", summary)
        self.assertIn("total", summary)
