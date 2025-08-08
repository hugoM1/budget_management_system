from decimal import Decimal
from django.test import TestCase, RequestFactory
from django.contrib.admin.sites import AdminSite
from campaigns.models import Brand, Campaign, Spend
from campaigns.admin import CampaignAdmin


class DummySite(AdminSite):
    pass


class AdminDisplayTests(TestCase):
    def setUp(self) -> None:
        self.site = DummySite()
        self.admin = CampaignAdmin(Campaign, self.site)
        self.brand = Brand.objects.create(name="ABrand", daily_budget=Decimal("200.00"), monthly_budget=Decimal("2000.00"))
        self.campaign = Campaign.objects.create(
            brand=self.brand,
            name="ACamp",
            status=Campaign.Status.ACTIVE,
            daily_budget=Decimal("100.00"),
            monthly_budget=Decimal("1000.00"),
        )

    def test_budget_utilization_green_under_80(self) -> None:
        Spend.objects.create(campaign=self.campaign, date=self._today(), daily_spend=Decimal("10.00"), monthly_spend=Decimal("10.00"))
        html = self.admin.budget_utilization(self.campaign)
        self.assertIn("%", html)
        self.assertIn("color:", html)

    def test_pause_reason_display_dash_when_none(self) -> None:
        html = self.admin.pause_reason_display(self.campaign)
        self.assertIn("-", str(html))

    def _today(self):
        from django.utils import timezone
        return timezone.now().date()
