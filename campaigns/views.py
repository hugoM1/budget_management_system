from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth import authenticate, login
from django.db.models import Sum, Q
from django.utils import timezone
from decimal import Decimal
from .models import Brand, Campaign, Spend, DaypartingSchedule

from django.http import HttpRequest, HttpResponse


def login_view(request: HttpRequest) -> HttpResponse:
    """Simple login view for testing."""
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            return redirect('campaigns:dashboard')
    
    return render(request, 'campaigns/login.html')

def dashboard(request: HttpRequest) -> HttpResponse:
    """Dashboard view showing budget management overview."""
    
    today = timezone.now().date()
    
    # Get summary statistics
    total_brands = Brand.objects.count()
    total_campaigns = Campaign.objects.count()
    active_campaigns = Campaign.objects.filter(status=Campaign.Status.ACTIVE).count()
    paused_campaigns = Campaign.objects.filter(status=Campaign.Status.PAUSED).count()
    
    # Get today's spend data
    today_spends = Spend.objects.filter(date=today)
    total_daily_spend = today_spends.aggregate(total=Sum('daily_spend'))['total'] or Decimal('0.00')
    total_monthly_spend = today_spends.aggregate(total=Sum('monthly_spend'))['total'] or Decimal('0.00')
    
    # Get brand summaries
    brands = Brand.objects.prefetch_related('campaigns').all()
    brand_summaries = []
    
    for brand in brands:
        brand_daily_spend = brand.get_total_daily_spend()
        brand_monthly_spend = brand.get_total_monthly_spend()
        brand_campaigns = brand.campaigns.all()
        
        brand_summaries.append({
            'brand': brand,
            'daily_spend': brand_daily_spend,
            'monthly_spend': brand_monthly_spend,
            'daily_budget_remaining': brand.daily_budget - brand_daily_spend,
            'monthly_budget_remaining': brand.monthly_budget - brand_monthly_spend,
            'campaign_count': brand_campaigns.count(),
            'active_campaigns': brand_campaigns.filter(status=Campaign.Status.ACTIVE).count(),
        })
    
    # Get campaigns that need attention
    campaigns_needing_attention = []
    
    for campaign in Campaign.objects.filter(status=Campaign.Status.ACTIVE):
        spend = campaign.get_current_spend()
        if spend:
            daily_remaining = campaign.daily_budget - spend.daily_spend
            monthly_remaining = campaign.monthly_budget - spend.monthly_spend
            
            if daily_remaining < Decimal('50.00') or monthly_remaining < Decimal('500.00'):
                campaigns_needing_attention.append({
                    'campaign': campaign,
                    'daily_remaining': daily_remaining,
                    'monthly_remaining': monthly_remaining,
                    'daily_spend': spend.daily_spend,
                    'monthly_spend': spend.monthly_spend,
                })
    
    # Get paused campaigns with reasons
    paused_campaigns_list = Campaign.objects.filter(
        status=Campaign.Status.PAUSED
    ).select_related('brand')
    
    context = {
        'total_brands': total_brands,
        'total_campaigns': total_campaigns,
        'active_campaigns': active_campaigns,
        'paused_campaigns': paused_campaigns,
        'total_daily_spend': total_daily_spend,
        'total_monthly_spend': total_monthly_spend,
        'brand_summaries': brand_summaries,
        'campaigns_needing_attention': campaigns_needing_attention,
        'paused_campaigns_list': paused_campaigns_list,
        'today': today,
    }
    
    return render(request, 'campaigns/dashboard.html', context)

@login_required
def brand_detail(request: HttpRequest, brand_id: int) -> HttpResponse:
    """Detailed view for a specific brand."""
    
    try:
        brand = Brand.objects.prefetch_related('campaigns').get(id=brand_id)
    except Brand.DoesNotExist:
        return render(request, 'campaigns/404.html', status=404)
    
    campaigns = brand.campaigns.all()
    today = timezone.now().date()
    
    # Get spend data for all campaigns
    campaign_data = []
    for campaign in campaigns:
        spend = campaign.get_current_spend()
        campaign_data.append({
            'campaign': campaign,
            'daily_spend': spend.daily_spend if spend else Decimal('0.00'),
            'monthly_spend': spend.monthly_spend if spend else Decimal('0.00'),
            'daily_remaining': campaign.daily_budget - (spend.daily_spend if spend else Decimal('0.00')),
            'monthly_remaining': campaign.monthly_budget - (spend.monthly_spend if spend else Decimal('0.00')),
        })
    
    context = {
        'brand': brand,
        'campaign_data': campaign_data,
        'today': today,
    }
    
    return render(request, 'campaigns/brand_detail.html', context)
