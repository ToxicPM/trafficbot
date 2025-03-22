import math
import random
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Any

# Get loggers
activity_logger = logging.getLogger("activity")
error_logger = logging.getLogger("error")

class TrafficScheduler:
    """Class for scheduling traffic generation based on targets and constraints."""
    
    def __init__(self):
        """Initialize the traffic scheduler."""
        self.target_visits = {
            'hourly': 0,
            'daily': 0,
            'monthly': 0,
            'total': 0
        }
        self.start_date = None
        self.end_date = None
        self.active_hours = list(range(24))  # Default to all hours
        self.active_days = list(range(7))    # Default to all days (0=Monday, 6=Sunday)
        self.schedule_mode = 'even'          # 'even', 'random', 'frontloaded', 'backloaded'
        
        # Tracking
        self.hourly_visits = 0
        self.daily_visits = 0
        self.monthly_visits = 0
        self.total_visits = 0
        self.last_hour = None
        self.last_day = None
        self.last_month = None
        
        # Store hourly distribution of visits
        self.hourly_targets = {}
        self.daily_targets = {}
    
    def set_target(self, period: str, value: int) -> None:
        """Set target visits for a specific period."""
        if period in self.target_visits:
            self.target_visits[period] = value
            activity_logger.info(f"Set {period} visit target to {value}")
            
            # Recalculate schedule when targets change
            self.calculate_schedule()
    
    def set_time_range(self, start_date, end_date) -> None:
        """Set the start and end date for the traffic campaign."""
        self.start_date = start_date
        self.end_date = end_date
        activity_logger.info(f"Set traffic schedule from {start_date} to {end_date}")
        
        # Recalculate schedule when dates change
        self.calculate_schedule()
    
    def set_active_hours(self, hours: list) -> None:
        """Set active hours (0-23) when the bot should generate traffic."""
        self.active_hours = hours
        activity_logger.info(f"Set active hours to {hours}")
        
        # Recalculate schedule when active hours change
        self.calculate_schedule()
    
    def set_active_days(self, days: list) -> None:
        """Set active days (0-6, Monday=0) when the bot should generate traffic."""
        self.active_days = days
        activity_logger.info(f"Set active days to {days}")
        
        # Recalculate schedule when active days change
        self.calculate_schedule()
    
    def set_schedule_mode(self, mode: str) -> None:
        """Set the schedule mode for distributing visits."""
        valid_modes = ['even', 'random', 'frontloaded', 'backloaded']
        if mode in valid_modes:
            self.schedule_mode = mode
            activity_logger.info(f"Set schedule mode to {mode}")
            
            # Recalculate schedule when mode changes
            self.calculate_schedule()
        else:
            error_logger.error(f"Invalid schedule mode: {mode}")
    
    def calculate_schedule(self) -> None:
        """Calculate the hourly distribution of visits based on targets and constraints."""
        import calendar
        now = datetime.now()
        
        # Use current month if no end date specified
        if not self.end_date:
            year = now.year
            month = now.month
            last_day = calendar.monthrange(year, month)[1]
            self.end_date = datetime(year, month, last_day, 23, 59, 59)
        
        # Use current date as start date if not specified
        if not self.start_date:
            self.start_date = now
        
        # Calculate total days in the campaign
        total_days = (self.end_date - self.start_date).days + 1
        active_days_count = sum(1 for d in range(total_days) if (self.start_date + timedelta(days=d)).weekday() in self.active_days)
        active_hours_count = len(self.active_hours)
        total_active_hours = active_days_count * active_hours_count
        
        # Calculate targets based on priority
        if self.target_visits['monthly'] > 0:
            # Monthly target is specified, calculate daily and hourly from it
            target_per_day = self.target_visits['monthly'] / active_days_count
            target_per_hour = target_per_day / active_hours_count
            
            self.target_visits['daily'] = math.ceil(target_per_day)
            self.target_visits['hourly'] = math.ceil(target_per_hour)
            self.target_visits['total'] = self.target_visits['monthly']
        
        elif self.target_visits['total'] > 0:
            # Total target is specified, calculate monthly, daily and hourly from it
            target_per_month = self.target_visits['total'] / ((total_days / 30) or 1)
            target_per_day = self.target_visits['total'] / active_days_count
            target_per_hour = target_per_day / active_hours_count
            
            self.target_visits['monthly'] = math.ceil(target_per_month)
            self.target_visits['daily'] = math.ceil(target_per_day)
            self.target_visits['hourly'] = math.ceil(target_per_hour)
        
        elif self.target_visits['daily'] > 0:
            # Daily target is specified, calculate hourly and monthly from it
            target_per_hour = self.target_visits['daily'] / active_hours_count
            target_per_month = self.target_visits['daily'] * (active_days_count / total_days) * 30
            target_total = self.target_visits['daily'] * active_days_count
            
            self.target_visits['hourly'] = math.ceil(target_per_hour)
            self.target_visits['monthly'] = math.ceil(target_per_month)
            self.target_visits['total'] = math.ceil(target_total)
        
        elif self.target_visits['hourly'] > 0:
            # Hourly target is specified, calculate daily, monthly and total from it
            target_per_day = self.target_visits['hourly'] * active_hours_count
            target_per_month = target_per_day * (active_days_count / total_days) * 30
            target_total = self.target_visits['hourly'] * total_active_hours
            
            self.target_visits['daily'] = math.ceil(target_per_day)
            self.target_visits['monthly'] = math.ceil(target_per_month)
            self.target_visits['total'] = math.ceil(target_total)
        
        # Calculate hourly distribution based on schedule mode
        self.hourly_targets = {}
        days_range = range((self.end_date - self.start_date).days + 1)
        
        if self.schedule_mode == 'even':
            # Distribute evenly across all active hours
            for day_offset in days_range:
                day = self.start_date + timedelta(days=day_offset)
                if day.weekday() in self.active_days:
                    for hour in self.active_hours:
                        hour_key = day.strftime('%Y-%m-%d') + f'-{hour}'
                        self.hourly_targets[hour_key] = self.target_visits['hourly']
        
        elif self.schedule_mode == 'random':
            # Distribute randomly but maintain daily targets
            for day_offset in days_range:
                day = self.start_date + timedelta(days=day_offset)
                if day.weekday() in self.active_days:
                    daily_target = self.target_visits['daily']
                    hours_for_day = [
                        day.strftime('%Y-%m-%d') + f'-{hour}' 
                        for hour in self.active_hours
                    ]
                    
                    # Distribute the daily target randomly across active hours
                    hourly_values = [0] * len(hours_for_day)
                    remaining = daily_target
                    
                    while remaining > 0:
                        idx = random.randint(0, len(hours_for_day) - 1)
                        hourly_values[idx] += 1
                        remaining -= 1
                    
                    for i, hour_key in enumerate(hours_for_day):
                        self.hourly_targets[hour_key] = hourly_values[i]
        
        elif self.schedule_mode == 'frontloaded':
            # More visits at the beginning, tapering off
            total_active_hours = sum(1 for d in days_range if (self.start_date + timedelta(days=d)).weekday() in self.active_days) * len(self.active_hours)
            total_target = self.target_visits['total']
            
            # Create a decreasing weight for each hour
            weights = []
            for day_offset in days_range:
                day = self.start_date + timedelta(days=day_offset)
                if day.weekday() in self.active_days:
                    for hour in self.active_hours:
                        hour_idx = day_offset * 24 + hour
                        weights.append((day.strftime('%Y-%m-%d') + f'-{hour}', 
                                       max(1, total_active_hours - hour_idx)))
            
            total_weight = sum(w[1] for w in weights)
            for hour_key, weight in weights:
                self.hourly_targets[hour_key] = math.ceil((weight / total_weight) * total_target)
        
        elif self.schedule_mode == 'backloaded':
            # Fewer visits at the beginning, ramping up
            total_active_hours = sum(1 for d in days_range if (self.start_date + timedelta(days=d)).weekday() in self.active_days) * len(self.active_hours)
            total_target = self.target_visits['total']
            
            # Create an increasing weight for each hour
            weights = []
            for day_offset in days_range:
                day = self.start_date + timedelta(days=day_offset)
                if day.weekday() in self.active_days:
                    for hour in self.active_hours:
                        hour_idx = day_offset * 24 + hour
                        weights.append((day.strftime('%Y-%m-%d') + f'-{hour}', 
                                       hour_idx + 1))
            
            total_weight = sum(w[1] for w in weights)
            for hour_key, weight in weights:
                self.hourly_targets[hour_key] = math.ceil((weight / total_weight) * total_target)
        
        activity_logger.info(f"Calculated visit schedule: {self.target_visits}")
    
    def should_generate_traffic(self) -> bool:
        """Check if we should generate traffic right now based on schedule and targets."""
        now = datetime.now()
        current_hour = now.hour
        current_day = now.weekday()
        current_hour_key = now.strftime('%Y-%m-%d') + f'-{current_hour}'
        
        # Check if we're within the campaign date range
        if self.start_date and now < self.start_date:
            return False
        
        if self.end_date and now > self.end_date:
            return False
        
        # Check if current hour and day are in the active ranges
        if current_hour not in self.active_hours or current_day not in self.active_days:
            return False
        
        # Check if we've reached the hourly target
        if current_hour_key in self.hourly_targets and self.hourly_visits >= self.hourly_targets[current_hour_key]:
            return False
        
        # Reset counters if the hour/day/month has changed
        if self.last_hour != current_hour:
            self.hourly_visits = 0
            self.last_hour = current_hour
        
        if self.last_day != now.day:
            self.daily_visits = 0
            self.last_day = now.day
        
        if self.last_month != now.month:
            self.monthly_visits = 0
            self.last_month = now.month
        
        return True
    
    def record_visit(self) -> None:
        """Record a visit for tracking against targets."""
        self.hourly_visits += 1
        self.daily_visits += 1
        self.monthly_visits += 1
        self.total_visits += 1
    
    def get_stats(self) -> dict:
        """Get current statistics about the traffic schedule."""
        now = datetime.now()
        current_hour_key = now.strftime('%Y-%m-%d') + f'-{now.hour}'
        
        stats = {
            'targets': self.target_visits.copy(),
            'current': {
                'hourly': self.hourly_visits,
                'daily': self.daily_visits,
                'monthly': self.monthly_visits,
                'total': self.total_visits
            },
            'progress': {
                'hourly': 0,
                'daily': 0,
                'monthly': 0,
                'total': 0
            },
            'hourly_target': self.hourly_targets.get(current_hour_key, 0),
            'schedule_mode': self.schedule_mode,
            'active_hours': self.active_hours,
            'active_days': self.active_days
        }
        
        # Calculate progress percentages
        if self.target_visits['hourly'] > 0:
            stats['progress']['hourly'] = min(100, round(self.hourly_visits / self.target_visits['hourly'] * 100))
        
        if self.target_visits['daily'] > 0:
            stats['progress']['daily'] = min(100, round(self.daily_visits / self.target_visits['daily'] * 100))
        
        if self.target_visits['monthly'] > 0:
            stats['progress']['monthly'] = min(100, round(self.monthly_visits / self.target_visits['monthly'] * 100))
        
        if self.target_visits['total'] > 0:
            stats['progress']['total'] = min(100, round(self.total_visits / self.target_visits['total'] * 100))
        
        return stats