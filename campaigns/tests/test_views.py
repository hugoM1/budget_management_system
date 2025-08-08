from decimal import Decimal
from django.test import TestCase
from django.urls import reverse
from django.contrib.auth.models import User
from campaigns.models import Brand, Campaign


class ViewTests(TestCase):
    def setUp(self) -> None:
        self.user = User.objects.create_user(username="tester", password="pass12345")
        self.client.force_login(self.user)
        self.brand = Brand.objects.create(name="VBrand", daily_budget=Decimal("100.00"), monthly_budget=Decimal("1000.00"))
        self.campaign = Campaign.objects.create(
            brand=self.brand,
            name="VCamp",
            status=Campaign.Status.ACTIVE,
            daily_budget=Decimal("50.00"),
            monthly_budget=Decimal("500.00"),
        )

    def test_dashboard_ok(self) -> None:
        resp = self.client.get(reverse("campaigns:dashboard"))
        self.assertEqual(resp.status_code, 200)
        for key in [
            "total_brands",
            "total_campaigns",
            "active_campaigns",
            "paused_campaigns",
            "brand_summaries",
        ]:
            self.assertIn(key, resp.context)

    def test_brand_detail_ok(self) -> None:
        url = reverse("campaigns:brand_detail", args=[self.brand.id])
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)

    def test_brand_detail_404(self) -> None:
        url = reverse("campaigns:brand_detail", args=[999999])
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, 404)
