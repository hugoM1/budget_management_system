from decimal import Decimal
from django.test import TestCase, override_settings
from campaigns.models import Brand, Campaign
from campaigns.tasks import (
    track_spend_task,
    check_budget_limits_task,
    simulate_spend_task,
    get_campaign_status_summary_task,
)


@override_settings(CELERY_TASK_ALWAYS_EAGER=True)
class TaskTests(TestCase):
    def setUp(self) -> None:
        self.brand = Brand.objects.create(name="B", daily_budget=Decimal("100.00"), monthly_budget=Decimal("1000.00"))
        self.campaign = Campaign.objects.create(
            brand=self.brand,
            name="C",
            status=Campaign.Status.ACTIVE,
            daily_budget=Decimal("50.00"),
            monthly_budget=Decimal("500.00"),
        )

    def test_track_spend_task(self) -> None:
        res = track_spend_task.delay(self.campaign.id, 5.0)
        self.assertTrue(res.status in ("PENDING", "SUCCESS"))

    def test_check_budget_limits_task(self) -> None:
        res = check_budget_limits_task.delay(self.campaign.id)
        self.assertTrue(res.status in ("PENDING", "SUCCESS"))

    def test_simulate_spend_task(self) -> None:
        res = simulate_spend_task.delay(self.campaign.id)
        self.assertTrue(res.status in ("PENDING", "SUCCESS"))

    def test_get_campaign_status_summary_task(self) -> None:
        res = get_campaign_status_summary_task.delay()
        self.assertTrue(res.status in ("PENDING", "SUCCESS"))
