// Wait for DOM to be fully loaded
document.addEventListener('DOMContentLoaded', function() {
    // Section navigation
    const sections = document.querySelectorAll('.section');
    const navLinks = document.querySelectorAll('.nav-link');
    
    navLinks.forEach(link => {
        link.addEventListener('click', function(e) {
            e.preventDefault();
            
            // Remove active class from all links and sections
            navLinks.forEach(link => link.classList.remove('active'));
            sections.forEach(section => section.classList.remove('active'));
            
            // Add active class to clicked link
            this.classList.add('active');
            
            // Get target section and show it
            const targetId = this.getAttribute('href').substring(1);
            document.getElementById(targetId).classList.add('active');
        });
    });
    
    // Generate hours checkboxes
    const hoursSelector = document.getElementById('hours-selector');
    if (hoursSelector) {
        for (let i = 0; i < 24; i++) {
            const hour = i.toString().padStart(2, '0');
            const checkbox = document.createElement('div');
            checkbox.classList.add('form-check', 'hour-checkbox');
            checkbox.innerHTML = `
                <input class="form-check-input active-hour" type="checkbox" value="${i}" id="hour-${i}" checked>
                <label class="form-check-label" for="hour-${i}">${hour}</label>
            `;
            hoursSelector.appendChild(checkbox);
        }
    }
    
    // Hour presets
    const hourPresets = document.querySelectorAll('.hour-preset');
    hourPresets.forEach(preset => {
        preset.addEventListener('click', function() {
            const presetType = this.getAttribute('data-hours');
            const hourCheckboxes = document.querySelectorAll('.active-hour');
            
            // Uncheck all hours first
            hourCheckboxes.forEach(cb => cb.checked = false);
            
            if (presetType === 'all') {
                // Check all hours
                hourCheckboxes.forEach(cb => cb.checked = true);
            } else if (presetType === 'business') {
                // Check business hours (9am-5pm)
                for (let i = 9; i <= 17; i++) {
                    document.getElementById(`hour-${i}`).checked = true;
                }
            } else if (presetType === 'evening') {
                // Check evening hours (6pm-11pm)
                for (let i = 18; i <= 23; i++) {
                    document.getElementById(`hour-${i}`).checked = true;
                }
            }
        });
    });
    
    // Initialize charts
    initCharts();
    
    // Load initial data
    loadStats();
    loadLogs();
    loadVPNData();
    loadProxyData();
    
    // Auto-refresh stats every 30 seconds
    setInterval(loadStats, 30000);
    
    // Setup event handlers
    setupEventHandlers();
});

// Initialize charts
function initCharts() {
    // Sources chart
    const sourcesCtx = document.getElementById('sources-chart')?.getContext('2d');
    if (sourcesCtx) {
        window.sourcesChart = new Chart(sourcesCtx, {
            type: 'doughnut',
            data: {
                labels: ['Search', 'Social', 'Direct', 'Referral'],
                datasets: [{
                    data: [40, 25, 20, 15],
                    backgroundColor: [
                        '#0d6efd',
                        '#6f42c1',
                        '#fd7e14',
                        '#20c997'
                    ]
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: true,
                plugins: {
                    legend: {
                        position: 'bottom'
                    }
                }
            }
        });
    }
    
    // Devices chart
    const devicesCtx = document.getElementById('devices-chart')?.getContext('2d');
    if (devicesCtx) {
        window.devicesChart = new Chart(devicesCtx, {
            type: 'doughnut',
            data: {
                labels: ['Desktop', 'Mobile', 'Tablet'],
                datasets: [{
                    data: [60, 30, 10],
                    backgroundColor: [
                        '#0d6efd',
                        '#dc3545',
                        '#ffc107'
                    ]
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: true,
                plugins: {
                    legend: {
                        position: 'bottom'
                    }
                }
            }
        });
    }
    
    // Success chart
    const successCtx = document.getElementById('success-chart')?.getContext('2d');
    if (successCtx) {
        window.successChart = new Chart(successCtx, {
            type: 'doughnut',
            data: {
                labels: ['Successful', 'Failed'],
                datasets: [{
                    data: [95, 5],
                    backgroundColor: [
                        '#198754',
                        '#dc3545'
                    ]
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: true,
                plugins: {
                    legend: {
                        position: 'bottom'
                    }
                }
            }
        });
    }
}

// Load bot statistics
function loadStats() {
    fetch('/api/bot/stats')
        .then(response => response.json())
        .then(data => {
            if (data.status === 'success') {
                updateStats(data.stats);
            }
        })
        .catch(error => console.error('Error fetching stats:', error));
        
    // Also update IP
    updateIP();
}

// Update statistics display
function updateStats(stats) {
    // Update counter displays
    document.getElementById('total-visits').textContent = stats.visits;
    document.getElementById('successful-visits').textContent = stats.successful_visits;
    document.getElementById('failed-visits').textContent = stats.failed_visits;
    document.getElementById('captchas-solved').textContent = stats.captchas_solved;
    
    // Update status display
    document.getElementById('bot-status').textContent = stats.running ? 
        (stats.paused ? 'Paused' : 'Running') : 'Stopped';
    
    // Update button states
    document.getElementById('start-bot').disabled = stats.running;
    document.getElementById('stop-bot').disabled = !stats.running;
    document.getElementById('pause-bot').disabled = !stats.running || stats.paused;
    document.getElementById('resume-bot').disabled = !stats.running || !stats.paused;
    
    // Update last visit time if available
    if (stats.last_visit) {
        document.getElementById('last-visit').textContent = stats.last_visit;
    }
    
    // Update charts if available
    if (window.sourcesChart) {
        const sourceData = [
            stats.search_traffic || 0,
            stats.social_traffic || 0,
            stats.direct_traffic || 0,
            stats.referral_traffic || 0
        ];
        window.sourcesChart.data.datasets[0].data = sourceData;
        window.sourcesChart.update();
    }
    
    if (window.devicesChart) {
        const deviceData = [
            stats.desktop_visits || 0,
            stats.mobile_visits || 0,
            stats.tablet_visits || 0
        ];
        window.devicesChart.data.datasets[0].data = deviceData;
        window.devicesChart.update();
    }
    
    if (window.successChart) {
        const successData = [
            stats.successful_visits || 0,
            stats.failed_visits || 0
        ];
        window.successChart.data.datasets[0].data = successData;
        window.successChart.update();
    }
    
    // Update scheduler stats if available
    if (stats.scheduler) {
        // Update monthly progress
        const monthlyProgress = document.getElementById('monthly-progress');
        if (monthlyProgress) {
            const progress = stats.scheduler.progress.monthly || 0;
            monthlyProgress.style.width = `${progress}%`;
            monthlyProgress.textContent = `${progress}%`;
            monthlyProgress.setAttribute('aria-valuenow', progress);
        }
    }
}

// Load log data
function loadLogs() {
    // Load activity log
    fetch('/api/logs/activity')
        .then(response => response.json())
        .then(data => {
            if (data.status === 'success') {
                const logContainer = document.getElementById('activity-log-container');
                logContainer.innerHTML = data.logs.join('');
                logContainer.scrollTop = logContainer.scrollHeight;
            }
        })
        .catch(error => console.error('Error fetching activity logs:', error));
        
    // Load error log
    fetch('/api/logs/error')
        .then(response => response.json())
        .then(data => {
            if (data.status === 'success') {
                const logContainer = document.getElementById('error-log-container');
                logContainer.innerHTML = data.logs.join('');
                logContainer.scrollTop = logContainer.scrollHeight;
            }
        })
        .catch(error => console.error('Error fetching error logs:', error));
}

// Update IP display
function updateIP() {
    fetch('/api/vpn/ip')
        .then(response => response.json())
        .then(data => {
            if (data.status === 'success') {
                document.getElementById('current-ip').textContent = `Current IP: ${data.ip}`;
            }
        })
        .catch(error => console.error('Error fetching IP:', error));
}

// Load VPN data
function loadVPNData() {
    // Load PIA regions
    fetch('/api/vpn/regions/pia')
        .then(response => response.json())
        .then(data => {
            if (data.status === 'success') {
                const select = document.getElementById('pia-region');
                if (select) {
                    // Clear existing options
                    select.innerHTML = '<option value="">Select Region</option>';
                    
                    // Add new options
                    data.regions.forEach(region => {
                        const option = document.createElement('option');
                        option.value = region;
                        option.textContent = region;
                        select.appendChild(option);
                    });
                }
            }
        })
        .catch(error => console.error('Error fetching PIA regions:', error));
        
    // Load NordVPN regions
    fetch('/api/vpn/regions/nordvpn')
        .then(response => response.json())
        .then(data => {
            if (data.status === 'success') {
                const select = document.getElementById('nordvpn-region');
                if (select) {
                    // Clear existing options
                    select.innerHTML = '<option value="">Select Region</option>';
                    
                    // Add new options
                    data.regions.forEach(region => {
                        const option = document.createElement('option');
                        option.value = region;
                        option.textContent = region;
                        select.appendChild(option);
                    });
                }
            }
        })
        .catch(error => console.error('Error fetching NordVPN regions:', error));
        
    // Load ExpressVPN regions
    fetch('/api/vpn/regions/expressvpn')
        .then(response => response.json())
        .then(data => {
            if (data.status === 'success') {
                const select = document.getElementById('expressvpn-region');
                if (select) {
                    // Clear existing options
                    select.innerHTML = '<option value="">Select Region</option>';
                    
                    // Add new options
                    data.regions.forEach(region => {
                        const option = document.createElement('option');
                        option.value = region;
                        option.textContent = region;
                        select.appendChild(option);
                    });
                }
            }
        })
        .catch(error => console.error('Error fetching ExpressVPN regions:', error));
}

// Load proxy data
function loadProxyData() {
    fetch('/api/proxies')
        .then(response => response.json())
        .then(data => {
            if (data.status === 'success') {
                document.getElementById('proxy-count').textContent = data.count;
                document.getElementById('current-proxy').textContent = data.current || 'None';
                document.getElementById('use-proxies').checked = data.use_proxies;
            }
        })
        .catch(error => console.error('Error fetching proxy data:', error));
}

// Setup event handlers
function setupEventHandlers() {
    // Start bot
    document.getElementById('start-bot')?.addEventListener('click', function() {
        const workerThreads = parseInt(document.getElementById('worker-threads').value) || 8;
        
        // Get keywords and URLs
        const keywords = document.getElementById('keywords').value.trim().split('\n').filter(k => k.trim());
        const urls = document.getElementById('urls').value.trim().split('\n').filter(u => u.trim());
        
        fetch('/api/bot/start', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                workers: workerThreads,
                keywords: keywords,
                urls: urls
            })
        })
        .then(response => response.json())
        .then(data => {
            alert(data.message);
            loadStats();
        })
        .catch(error => console.error('Error starting bot:', error));
    });
    
    // Stop bot
    document.getElementById('stop-bot')?.addEventListener('click', function() {
        fetch('/api/bot/stop', {
            method: 'POST'
        })
        .then(response => response.json())
        .then(data => {
            alert(data.message);
            loadStats();
        })
        .catch(error => console.error('Error stopping bot:', error));
    });
    
    // Pause bot
    document.getElementById('pause-bot')?.addEventListener('click', function() {
        fetch('/api/bot/pause', {
            method: 'POST'
        })
        .then(response => response.json())
        .then(data => {
            alert(data.message);
            loadStats();
        })
        .catch(error => console.error('Error pausing bot:', error));
    });
    
    // Resume bot
    document.getElementById('resume-bot')?.addEventListener('click', function() {
        fetch('/api/bot/resume', {
            method: 'POST'
        })
        .then(response => response.json())
        .then(data => {
            alert(data.message);
            loadStats();
        })
        .catch(error => console.error('Error resuming bot:', error));
    });
    
    // Update keywords
    document.getElementById('update-keywords')?.addEventListener('click', function() {
        const keywords = document.getElementById('keywords').value.trim().split('\n').filter(k => k.trim());
        
        fetch('/api/bot/keywords', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ keywords: keywords })
        })
        .then(response => response.json())
        .then(data => {
            alert(data.message);
        })
        .catch(error => console.error('Error updating keywords:', error));
    });
    
    // Update URLs
    document.getElementById('update-urls')?.addEventListener('click', function() {
        const urls = document.getElementById('urls').value.trim().split('\n').filter(u => u.trim());
        
        fetch('/api/bot/urls', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ urls: urls })
        })
        .then(response => response.json())
        .then(data => {
            alert(data.message);
        })
        .catch(error => console.error('Error updating URLs:', error));
    });
    
    // Add tracking URL
    document.getElementById('add-tracking-url')?.addEventListener('click', function() {
        const originalUrl = document.getElementById('original-url').value.trim();
        const trackingUrl = document.getElementById('tracking-url').value.trim();
        
        if (!originalUrl || !trackingUrl) {
            alert('Both Original URL and Tracking URL are required');
            return;
        }
        
        fetch('/api/bot/tracking', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                original_url: originalUrl,
                tracking_url: trackingUrl
            })
        })
        .then(response => response.json())
        .then(data => {
            alert(data.message);
            // Clear inputs
            document.getElementById('original-url').value = '';
            document.getElementById('tracking-url').value = '';
            // Reload tracking URLs
            loadTrackingUrls();
        })
        .catch(error => console.error('Error adding tracking URL:', error));
    });
    
    // Enable/disable VPN providers
    document.getElementById('enable-pia')?.addEventListener('change', function() {
        toggleVPN('pia', this.checked);
    });
    
    document.getElementById('enable-nordvpn')?.addEventListener('change', function() {
        toggleVPN('nordvpn', this.checked);
    });
    
    document.getElementById('enable-expressvpn')?.addEventListener('change', function() {
        toggleVPN('expressvpn', this.checked);
    });
    
    // Connect VPN buttons
    document.getElementById('connect-pia')?.addEventListener('click', function() {
        connectVPN('pia', document.getElementById('pia-region').value);
    });
    
    document.getElementById('connect-nordvpn')?.addEventListener('click', function() {
        connectVPN('nordvpn', document.getElementById('nordvpn-region').value);
    });
    
    document.getElementById('connect-expressvpn')?.addEventListener('click', function() {
        connectVPN('expressvpn', document.getElementById('expressvpn-region').value);
    });
    
    // Toggle proxy usage
    document.getElementById('use-proxies')?.addEventListener('change', function() {
        fetch('/api/proxies/toggle', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ use_proxies: this.checked })
        })
        .then(response => response.json())
        .then(data => {
            if (data.status === 'success') {
                console.log(`Proxy usage ${data.use_proxies ? 'enabled' : 'disabled'}`);
            }
        })
        .catch(error => console.error('Error toggling proxies:', error));
    });
    
    // Reload proxies
    document.getElementById('reload-proxies')?.addEventListener('click', function() {
        fetch('/api/proxies/reload', {
            method: 'POST'
        })
        .then(response => response.json())
        .then(data => {
            alert(data.message);
            loadProxyData();
        })
        .catch(error => console.error('Error reloading proxies:', error));
    });
    
    // Test random proxy
    document.getElementById('test-proxy')?.addEventListener('click', function() {
        fetch('/api/proxies/test', {
            method: 'POST'
        })
        .then(response => response.json())
        .then(data => {
            if (data.status === 'success') {
                alert(`Proxy: ${data.proxy}\nIP: ${data.ip}\nResponse Time: ${data.response_time}s`);
                loadProxyData();
                updateIP();
            } else {
                alert(`Error: ${data.message}`);
            }
        })
        .catch(error => console.error('Error testing proxy:', error));
    });
    
    // Update behavior settings
    document.getElementById('update-behavior')?.addEventListener('click', function() {
        const behaviorSettings = {
            min_visit_duration: parseInt(document.getElementById('min-duration').value) || 60,
            max_visit_duration: parseInt(document.getElementById('max-duration').value) || 180,
            bounce_rate: parseFloat(document.getElementById('bounce-rate').value) / 100 || 0.15,
            max_subpages: parseInt(document.getElementById('max-subpages').value) || 3,
            scroll_depth: parseInt(document.getElementById('scroll-depth').value) || 70,
            click_probability: parseFloat(document.getElementById('click-probability').value) / 100 || 0.6,
            form_interaction_probability: parseFloat(document.getElementById('form-interaction').value) / 100 || 0.3,
            adsense_safe: document.getElementById('adsense-safe').checked,
            device_types: {
                desktop: parseFloat(document.getElementById('desktop-percent').value) / 100 || 0.6,
                mobile: parseFloat(document.getElementById('mobile-percent').value) / 100 || 0.3,
                tablet: parseFloat(document.getElementById('tablet-percent').value) / 100 || 0.1
            },
            referrer_types: {
                search: parseFloat(document.getElementById('search-percent').value) / 100 || 0.4,
                social: parseFloat(document.getElementById('social-percent').value) / 100 || 0.25,
                direct: parseFloat(document.getElementById('direct-percent').value) / 100 || 0.2,
                referral: parseFloat(document.getElementById('referral-percent').value) / 100 || 0.15
            }
        };
        
        fetch('/api/behavior', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(behaviorSettings)
        })
        .then(response => response.json())
        .then(data => {
            alert(data.message);
        })
        .catch(error => console.error('Error updating behavior settings:', error));
    });
    
    // Update schedule
    document.getElementById('update-schedule')?.addEventListener('click', function() {
        const monthlyTarget = parseInt(document.getElementById('monthly-target').value) || 0;
        const scheduleMode = document.getElementById('schedule-mode').value;
        
        // Get active days
        const activeDays = Array.from(document.querySelectorAll('.active-day:checked'))
            .map(cb => parseInt(cb.value));
            
        // Get active hours
        const activeHours = Array.from(document.querySelectorAll('.active-hour:checked'))
            .map(cb => parseInt(cb.value));
            
        // Get date range
        const startDate = document.getElementById('start-date').value;
        const endDate = document.getElementById('end-date').value;
        
        const scheduleSettings = {
            targets: {
                monthly: monthlyTarget
            },
            schedule_mode: scheduleMode,
            active_days: activeDays,
            active_hours: activeHours
        };
        
        if (startDate) {
            scheduleSettings.start_date = startDate;
        }
        
        if (endDate) {
            scheduleSettings.end_date = endDate;
        }
        
        fetch('/api/schedule', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(scheduleSettings)
        })
        .then(response => response.json())
        .then(data => {
            alert(data.message);
            loadStats();
        })
        .catch(error => console.error('Error updating schedule:', error));
    });
    
    // Refresh logs
    document.getElementById('refresh-activity-log')?.addEventListener('click', function() {
        fetch('/api/logs/activity')
            .then(response => response.json())
            .then(data => {
                if (data.status === 'success') {
                        const logContainer = document.getElementById('activity-log-container');
                        logContainer.innerHTML = data.logs.join('');
                        logContainer.scrollTop = logContainer.scrollHeight;
                    }
                })
                .catch(error => console.error('Error fetching activity logs:', error));
    });
    
    document.getElementById('refresh-error-log')?.addEventListener('click', function() {
        fetch('/api/logs/error')
            .then(response => response.json())
            .then(data => {
                if (data.status === 'success') {
                    const logContainer = document.getElementById('error-log-container');
                    logContainer.innerHTML = data.logs.join('');
                    logContainer.scrollTop = logContainer.scrollHeight;
                }
            })
            .catch(error => console.error('Error fetching error logs:', error));
    });
    
    // Clear logs
    document.getElementById('clear-activity-log')?.addEventListener('click', function() {
        if (confirm('Are you sure you want to clear the activity log?')) {
            fetch('/api/logs/clear', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ type: 'activity' })
            })
            .then(response => response.json())
            .then(data => {
                alert(data.message);
                loadLogs();
            })
            .catch(error => console.error('Error clearing logs:', error));
        }
    });
    
    document.getElementById('clear-error-log')?.addEventListener('click', function() {
        if (confirm('Are you sure you want to clear the error log?')) {
            fetch('/api/logs/clear', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ type: 'error' })
            })
            .then(response => response.json())
            .then(data => {
                alert(data.message);
                loadLogs();
            })
            .catch(error => console.error('Error clearing logs:', error));
        }
    });
    
    // Load tracking URLs
    loadTrackingUrls();
    
    // Load behavior settings
    loadBehaviorSettings();
    
    // Load schedule settings
    loadScheduleSettings();
    
    // Initialize form validation
    initFormValidation();

    // Initialize device distribution sliders
    initDeviceSliders();
    
    // Initialize traffic source sliders
    initSourceSliders();
}

// Toggle VPN provider
function toggleVPN(provider, enabled) {
    const endpoint = enabled ? `/api/vpn/enable/${provider}` : `/api/vpn/disable/${provider}`;
    
    fetch(endpoint, {
        method: 'POST'
    })
    .then(response => response.json())
    .then(data => {
        console.log(data.message);
    })
    .catch(error => console.error(`Error ${enabled ? 'enabling' : 'disabling'} ${provider}:`, error));
}

// Connect to VPN
function connectVPN(provider, region) {
    if (!region) {
        alert(`Please select a ${provider.toUpperCase()} region`);
        return;
    }
    
    // Show connecting message
    document.getElementById(`${provider}-status`).textContent = 'Connecting...';
    
    fetch('/api/vpn/connect', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ provider, region })
    })
    .then(response => response.json())
    .then(data => {
        if (data.status === 'success') {
            document.getElementById(`${provider}-status`).textContent = `Connected to ${region}`;
            document.getElementById('current-ip').textContent = `Current IP: ${data.ip}`;
        } else {
            document.getElementById(`${provider}-status`).textContent = `Connection failed`;
            alert(`Failed to connect to ${provider}: ${data.message}`);
        }
    })
    .catch(error => {
        console.error(`Error connecting to ${provider}:`, error);
        document.getElementById(`${provider}-status`).textContent = `Connection error`;
    });
}

// Disconnect from all VPNs
function disconnectAllVPNs() {
    fetch('/api/vpn/disconnect', {
        method: 'POST'
    })
    .then(response => response.json())
    .then(data => {
        if (data.status === 'success') {
            document.getElementById('pia-status').textContent = 'Disconnected';
            document.getElementById('nordvpn-status').textContent = 'Disconnected';
            document.getElementById('expressvpn-status').textContent = 'Disconnected';
            document.getElementById('current-ip').textContent = `Current IP: ${data.ip}`;
            alert('Disconnected from all VPNs');
        } else {
            alert(`Failed to disconnect: ${data.message}`);
        }
    })
    .catch(error => console.error('Error disconnecting from VPNs:', error));
}

// Load tracking URLs
function loadTrackingUrls() {
    fetch('/api/bot/tracking')
        .then(response => response.json())
        .then(data => {
            if (data.status === 'success') {
                const trackingUrlsTable = document.getElementById('tracking-urls-body');
                if (trackingUrlsTable) {
                    trackingUrlsTable.innerHTML = '';
                    
                    const trackingUrls = data.tracking_urls;
                    for (const [originalUrl, trackingUrl] of Object.entries(trackingUrls)) {
                        const row = document.createElement('tr');
                        row.innerHTML = `
                            <td class="truncate-url" title="${originalUrl}">${originalUrl}</td>
                            <td class="truncate-url" title="${trackingUrl}">${trackingUrl}</td>
                            <td>
                                <button class="btn btn-sm btn-danger remove-tracking-url" data-url="${originalUrl}">
                                    <i class="fas fa-trash-alt"></i>
                                </button>
                            </td>
                        `;
                        trackingUrlsTable.appendChild(row);
                    }
                    
                    // Add event listeners to remove buttons
                    document.querySelectorAll('.remove-tracking-url').forEach(button => {
                        button.addEventListener('click', function() {
                            const url = this.getAttribute('data-url');
                            removeTrackingUrl(url);
                        });
                    });
                }
            }
        })
        .catch(error => console.error('Error loading tracking URLs:', error));
}

// Remove tracking URL
function removeTrackingUrl(url) {
    if (confirm(`Are you sure you want to remove the tracking URL for ${url}?`)) {
        fetch(`/api/bot/tracking/${encodeURIComponent(url)}`, {
            method: 'DELETE'
        })
        .then(response => response.json())
        .then(data => {
            alert(data.message);
            loadTrackingUrls();
        })
        .catch(error => console.error('Error removing tracking URL:', error));
    }
}

// Load behavior settings
function loadBehaviorSettings() {
    fetch('/api/behavior')
        .then(response => response.json())
        .then(data => {
            if (data.status === 'success') {
                const behavior = data.behavior;
                
                // Set form values
                document.getElementById('min-duration').value = behavior.min_visit_duration;
                document.getElementById('max-duration').value = behavior.max_visit_duration;
                document.getElementById('bounce-rate').value = (behavior.bounce_rate * 100).toFixed(0);
                document.getElementById('max-subpages').value = behavior.max_subpage_visits;
                document.getElementById('scroll-depth').value = behavior.scroll_depth;
                document.getElementById('click-probability').value = (behavior.click_probability * 100).toFixed(0);
                document.getElementById('form-interaction').value = (behavior.form_interaction_probability * 100).toFixed(0);
                document.getElementById('adsense-safe').checked = behavior.adsense_safe;
                
                // Set device percentages
                document.getElementById('desktop-percent').value = (behavior.device_types.desktop * 100).toFixed(0);
                document.getElementById('mobile-percent').value = (behavior.device_types.mobile * 100).toFixed(0);
                document.getElementById('tablet-percent').value = (behavior.device_types.tablet * 100).toFixed(0);
                
                // Update device labels
                document.querySelector('.desktop-value').textContent = `${(behavior.device_types.desktop * 100).toFixed(0)}%`;
                document.querySelector('.mobile-value').textContent = `${(behavior.device_types.mobile * 100).toFixed(0)}%`;
                document.querySelector('.tablet-value').textContent = `${(behavior.device_types.tablet * 100).toFixed(0)}%`;
                
                // Set source percentages
                document.getElementById('search-percent').value = (behavior.referrer_types.search * 100).toFixed(0);
                document.getElementById('social-percent').value = (behavior.referrer_types.social * 100).toFixed(0);
                document.getElementById('direct-percent').value = (behavior.referrer_types.direct * 100).toFixed(0);
                document.getElementById('referral-percent').value = (behavior.referrer_types.referral * 100).toFixed(0);
                
                // Update source labels
                document.querySelector('.search-value').textContent = `${(behavior.referrer_types.search * 100).toFixed(0)}%`;
                document.querySelector('.social-value').textContent = `${(behavior.referrer_types.social * 100).toFixed(0)}%`;
                document.querySelector('.direct-value').textContent = `${(behavior.referrer_types.direct * 100).toFixed(0)}%`;
                document.querySelector('.referral-value').textContent = `${(behavior.referrer_types.referral * 100).toFixed(0)}%`;
            }
        })
        .catch(error => console.error('Error loading behavior settings:', error));
}

// Load schedule settings
function loadScheduleSettings() {
    fetch('/api/schedule')
        .then(response => response.json())
        .then(data => {
            if (data.status === 'success') {
                const schedule = data.schedule;
                
                // Set form values
                document.getElementById('monthly-target').value = schedule.targets.monthly;
                document.getElementById('schedule-mode').value = schedule.schedule_mode;
                
                // Set active days
                document.querySelectorAll('.active-day').forEach(checkbox => {
                    checkbox.checked = schedule.active_days.includes(parseInt(checkbox.value));
                });
                
                // Set active hours
                document.querySelectorAll('.active-hour').forEach(checkbox => {
                    checkbox.checked = schedule.active_hours.includes(parseInt(checkbox.value));
                });
                
                // Set date range
                if (schedule.start_date) {
                    document.getElementById('start-date').value = schedule.start_date.substring(0, 10);
                }
                
                if (schedule.end_date) {
                    document.getElementById('end-date').value = schedule.end_date.substring(0, 10);
                }
            }
        })
        .catch(error => console.error('Error loading schedule settings:', error));
}

// Initialize form validation
function initFormValidation() {
    // Validate min/max duration
    document.getElementById('max-duration')?.addEventListener('change', function() {
        const minDuration = parseInt(document.getElementById('min-duration').value) || 0;
        const maxDuration = parseInt(this.value) || 0;
        
        if (maxDuration < minDuration) {
            alert('Maximum duration cannot be less than minimum duration');
            this.value = minDuration;
        }
    });
    
    document.getElementById('min-duration')?.addEventListener('change', function() {
        const minDuration = parseInt(this.value) || 0;
        const maxDuration = parseInt(document.getElementById('max-duration').value) || 0;
        
        if (minDuration > maxDuration && maxDuration > 0) {
            alert('Minimum duration cannot be greater than maximum duration');
            this.value = maxDuration;
        }
    });
    
    // Validate percentages
    const percentInputs = document.querySelectorAll('input[type="number"][max="100"]');
    percentInputs.forEach(input => {
        input.addEventListener('change', function() {
            const value = parseInt(this.value) || 0;
            if (value < 0) {
                this.value = 0;
            } else if (value > 100) {
                this.value = 100;
            }
        });
    });
}

// Initialize device distribution sliders
function initDeviceSliders() {
    const deviceSliders = document.querySelectorAll('.device-percent');
    
    deviceSliders.forEach(slider => {
        slider.addEventListener('input', function() {
            // Update value display
            const deviceType = this.id.replace('-percent', '');
            document.querySelector(`.${deviceType}-value`).textContent = `${this.value}%`;
            
            // Calculate total
            const desktopVal = parseInt(document.getElementById('desktop-percent').value) || 0;
            const mobileVal = parseInt(document.getElementById('mobile-percent').value) || 0;
            const tabletVal = parseInt(document.getElementById('tablet-percent').value) || 0;
            
            const total = desktopVal + mobileVal + tabletVal;
            
            // Alert if total is not 100%
            if (total !== 100) {
                document.getElementById('device-total-warning').textContent = `Total: ${total}% (should be 100%)`;
                document.getElementById('device-total-warning').style.display = 'block';
            } else {
                document.getElementById('device-total-warning').style.display = 'none';
            }
        });
    });
}

// Initialize traffic source sliders
function initSourceSliders() {
    const sourceSliders = document.querySelectorAll('.source-percent');
    
    sourceSliders.forEach(slider => {
        slider.addEventListener('input', function() {
            // Update value display
            const sourceType = this.id.replace('-percent', '');
            document.querySelector(`.${sourceType}-value`).textContent = `${this.value}%`;
            
            // Calculate total
            const searchVal = parseInt(document.getElementById('search-percent').value) || 0;
            const socialVal = parseInt(document.getElementById('social-percent').value) || 0;
            const directVal = parseInt(document.getElementById('direct-percent').value) || 0;
            const referralVal = parseInt(document.getElementById('referral-percent').value) || 0;
            
            const total = searchVal + socialVal + directVal + referralVal;
            
            // Alert if total is not 100%
            if (total !== 100) {
                document.getElementById('source-total-warning').textContent = `Total: ${total}% (should be 100%)`;
                document.getElementById('source-total-warning').style.display = 'block';
            } else {
                document.getElementById('source-total-warning').style.display = 'none';
            }
        });
    });
}