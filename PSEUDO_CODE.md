# Budget Management System - Pseudo Code

## Data Models

### Brand
```
Brand {
    id: unique identifier
    name: string
    daily_budget: decimal
    monthly_budget: decimal
    created_at: timestamp
    updated_at: timestamp
}
```

### Campaign
```
Campaign {
    id: unique identifier
    brand_id: foreign key to Brand
    name: string
    status: enum (ACTIVE, INACTIVE, PAUSED)
    daily_budget: decimal
    monthly_budget: decimal
    created_at: timestamp
    updated_at: timestamp
}
```

### Spend
```
Spend {
    id: unique identifier
    campaign_id: foreign key to Campaign
    date: date
    daily_spend: decimal
    monthly_spend: decimal
    created_at: timestamp
    updated_at: timestamp
}
```

### DaypartingSchedule
```
DaypartingSchedule {
    id: unique identifier
    campaign_id: foreign key to Campaign
    day_of_week: integer (0-6, where 0 is Monday)
    start_time: time
    end_time: time
    is_active: boolean
    created_at: timestamp
    updated_at: timestamp
}
```

## Key Logic

### 1. Spend Tracking Logic
```
FUNCTION track_spend(campaign_id, amount):
    current_time = get_current_utc_time()
    current_date = current_time.date()
    
    // Get or create spend record for today
    spend_record = get_or_create_spend(campaign_id, current_date)
    
    // Update daily spend
    spend_record.daily_spend += amount
    
    // Update monthly spend (reset on 1st of month)
    if current_date.day == 1:
        spend_record.monthly_spend = amount
    else:
        spend_record.monthly_spend += amount
    
    spend_record.save()
    
    // Check budget limits
    check_budget_limits(campaign_id)
```

### 2. Budget Enforcement Logic
```
FUNCTION check_budget_limits(campaign_id):
    campaign = get_campaign(campaign_id)
    spend_record = get_current_spend(campaign_id)
    
    // Check daily budget
    if spend_record.daily_spend >= campaign.daily_budget:
        pause_campaign(campaign_id, "DAILY_BUDGET_EXCEEDED")
        return
    
    // Check monthly budget
    if spend_record.monthly_spend >= campaign.monthly_budget:
        pause_campaign(campaign_id, "MONTHLY_BUDGET_EXCEEDED")
        return
    
    // If campaign was paused due to budget, reactivate if within limits
    if campaign.status == PAUSED and is_budget_available(campaign_id):
        activate_campaign(campaign_id)
```

### 3. Dayparting Check Logic
```
FUNCTION check_dayparting(campaign_id):
    current_time = get_current_utc_time()
    day_of_week = current_time.weekday()
    current_time_only = current_time.time()
    
    // Get dayparting schedules for this campaign and day
    schedules = get_dayparting_schedules(campaign_id, day_of_week)
    
    if schedules is empty:
        return true  // No restrictions
    
    for schedule in schedules:
        if schedule.is_active and 
           current_time_only >= schedule.start_time and 
           current_time_only <= schedule.end_time:
            return true
    
    return false  // Outside allowed hours
```

### 4. Daily Reset Logic
```
FUNCTION daily_reset():
    current_date = get_current_utc_date()
    
    // Reset all daily spends to 0
    for spend_record in get_all_spends():
        spend_record.daily_spend = 0
        spend_record.save()
    
    // Reactivate campaigns that were paused due to daily budget
    for campaign in get_paused_campaigns():
        if campaign.pause_reason == "DAILY_BUDGET_EXCEEDED":
            if is_budget_available(campaign.id):
                activate_campaign(campaign.id)
```

### 5. Monthly Reset Logic
```
FUNCTION monthly_reset():
    current_date = get_current_utc_date()
    
    // Only run on 1st of month
    if current_date.day != 1:
        return
    
    // Reset all monthly spends to 0
    for spend_record in get_all_spends():
        spend_record.monthly_spend = 0
        spend_record.save()
    
    // Reactivate campaigns that were paused due to monthly budget
    for campaign in get_paused_campaigns():
        if campaign.pause_reason == "MONTHLY_BUDGET_EXCEEDED":
            if is_budget_available(campaign.id):
                activate_campaign(campaign.id)
```

### 6. Campaign Status Management
```
FUNCTION activate_campaign(campaign_id):
    campaign = get_campaign(campaign_id)
    campaign.status = ACTIVE
    campaign.pause_reason = null
    campaign.save()
    
    log_campaign_status_change(campaign_id, "ACTIVATED")

FUNCTION pause_campaign(campaign_id, reason):
    campaign = get_campaign(campaign_id)
    campaign.status = PAUSED
    campaign.pause_reason = reason
    campaign.save()
    
    log_campaign_status_change(campaign_id, "PAUSED", reason)
```

### 7. Periodic Task Logic
```
FUNCTION periodic_budget_check():
    current_time = get_current_utc_time()
    
    for campaign in get_active_campaigns():
        // Check dayparting
        if not check_dayparting(campaign.id):
            pause_campaign(campaign.id, "OUTSIDE_DAYPARTING_HOURS")
            continue
        
        // Simulate spend for active campaigns
        if campaign.status == ACTIVE:
            simulate_spend(campaign.id)
    
    // Check for budget overruns
    for campaign in get_active_campaigns():
        check_budget_limits(campaign.id)
```

### 8. Spend Simulation Logic
```
FUNCTION simulate_spend(campaign_id):
    // Simulate spend based on campaign activity
    // In real implementation, this would come from actual ad serving data
    
    base_spend_rate = 0.01  // $0.01 per minute
    spend_amount = base_spend_rate * random_factor(0.5, 1.5)
    
    track_spend(campaign_id, spend_amount)
```

## System Workflow

### Daily Operations (00:00 UTC)
1. **Daily Reset**: Reset all daily spend records to 0
2. **Campaign Reactivation**: Reactivate campaigns paused due to daily budget limits
3. **Continuous Monitoring**: Every minute, check active campaigns for budget compliance

### Monthly Operations (1st of month, 00:00 UTC)
1. **Monthly Reset**: Reset all monthly spend records to 0
2. **Campaign Reactivation**: Reactivate campaigns paused due to monthly budget limits

### Real-time Operations (Every minute)
1. **Dayparting Check**: Verify campaigns are running within allowed hours
2. **Spend Tracking**: Update spend records for active campaigns
3. **Budget Enforcement**: Pause campaigns that exceed budget limits
4. **Status Updates**: Log all status changes for monitoring

## Assumptions and Simplifications

1. **Timezone**: All times stored and processed in UTC
2. **Spend Simulation**: Spend is simulated rather than coming from real ad serving data
3. **Budget Granularity**: Budgets are tracked at campaign level
4. **Dayparting**: Simple time window approach (can be extended to complex schedules)
5. **Error Handling**: Basic error handling with logging
6. **Concurrency**: Single-threaded approach for simplicity
7. **Database**: Using PostgreSQL for production-ready development

## Performance Considerations

1. **Indexing**: Index on campaign_id, date, and status fields
2. **Batch Operations**: Use bulk operations for resets
3. **Caching**: Cache frequently accessed campaign and budget data
4. **Monitoring**: Log all budget and status changes for analysis 