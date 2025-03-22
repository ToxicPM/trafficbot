import time
import os
from flask import request, jsonify
from app import app, vpn_manager

# Get loggers
activity_logger = logging.getLogger("activity")
error_logger = logging.getLogger("error")

@app.route('/api/vpn/ip', methods=['GET'])
def get_current_ip():
    """Get the current public IP address."""
    try:
        ip = vpn_manager.get_current_ip()
        return jsonify({
            "status": "success",
            "ip": ip
        })
    except Exception as e:
        error_logger.error(f"Error getting current IP: {str(e)}")
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route('/api/vpn/regions/<provider>', methods=['GET'])
def get_vpn_regions(provider):
    """Get regions for a specific VPN provider."""
    try:
        if provider not in vpn_manager.vpn_providers:
            return jsonify({
                "status": "error", 
                "message": f"Unknown VPN provider: {provider}"
            }), 400
        
        # Load regions if needed
        if not vpn_manager.vpn_providers[provider]['regions']:
            vpn_manager.load_vpn_regions(provider)
        
        regions = vpn_manager.vpn_providers[provider]['regions']
        
        return jsonify({
            "status": "success",
            "provider": provider,
            "regions": regions
        })
    except Exception as e:
        error_logger.error(f"Error getting VPN regions: {str(e)}")
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route('/api/vpn/enable/<provider>', methods=['POST'])
def enable_vpn_provider(provider):
    """Enable a VPN provider."""
    try:
        if provider not in vpn_manager.vpn_providers:
            return jsonify({
                "status": "error", 
                "message": f"Unknown VPN provider: {provider}"
            }), 400
        
        success = vpn_manager.enable_vpn(provider)
        
        if success:
            return jsonify({
                "status": "success",
                "message": f"Enabled VPN provider: {provider}"
            })
        else:
            return jsonify({
                "status": "error",
                "message": f"Failed to enable VPN provider: {provider}"
            }), 500
    except Exception as e:
        error_logger.error(f"Error enabling VPN provider: {str(e)}")
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route('/api/vpn/disable/<provider>', methods=['POST'])
def disable_vpn_provider(provider):
    """Disable a VPN provider."""
    try:
        if provider not in vpn_manager.vpn_providers:
            return jsonify({
                "status": "error", 
                "message": f"Unknown VPN provider: {provider}"
            }), 400
        
        success = vpn_manager.disable_vpn(provider)
        
        if success:
            return jsonify({
                "status": "success",
                "message": f"Disabled VPN provider: {provider}"
            })
        else:
            return jsonify({
                "status": "error",
                "message": f"Failed to disable VPN provider: {provider}"
            }), 500
    except Exception as e:
        error_logger.error(f"Error disabling VPN provider: {str(e)}")
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route('/api/vpn/connect', methods=['POST'])
def connect_vpn():
    """Connect to a VPN provider and region."""
    try:
        data = request.json
        if not data or 'provider' not in data or 'region' not in data:
            return jsonify({
                "status": "error", 
                "message": "Provider and region must be specified"
            }), 400
        
        provider = data['provider']
        region = data['region']
        
        if provider not in vpn_manager.vpn_providers:
            return jsonify({
                "status": "error", 
                "message": f"Unknown VPN provider: {provider}"
            }), 400
        
        success = vpn_manager.connect_vpn(provider, region)
        
        if success:
            return jsonify({
                "status": "success",
                "message": f"Connected to {provider} region: {region}",
                "ip": vpn_manager.get_current_ip()
            })
        else:
            return jsonify({
                "status": "error",
                "message": f"Failed to connect to {provider} region: {region}"
            }), 500
    except Exception as e:
        error_logger.error(f"Error connecting to VPN: {str(e)}")
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route('/api/vpn/disconnect', methods=['POST'])
def disconnect_vpn():
    """Disconnect from all VPNs."""
    try:
        success = vpn_manager.disconnect_all_vpns()
        
        if success:
            return jsonify({
                "status": "success",
                "message": "Disconnected from all VPNs",
                "ip": vpn_manager.get_current_ip()
            })
        else:
            return jsonify({
                "status": "error",
                "message": "Failed to disconnect from VPNs"
            }), 500
    except Exception as e:
        error_logger.error(f"Error disconnecting from VPN: {str(e)}")
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route('/api/proxies', methods=['GET'])
def get_proxies():
    """Get the list of loaded proxies."""
    try:
        # Return the count and the first few proxies (for privacy/security, don't return all)
        proxy_count = len(vpn_manager.proxies)
        proxy_sample = vpn_manager.proxies[:5] if proxy_count > 0 else []
        
        # Mask usernames and passwords in the sample
        masked_proxies = []
        for proxy in proxy_sample:
            if '@' in proxy:
                # Mask auth credentials
                parts = proxy.split('@')
                masked = 'http://***:***@' + parts[1]
                masked_proxies.append(masked)
            else:
                masked_proxies.append(proxy)
        
        return jsonify({
            "status": "success",
            "count": proxy_count,
            "current": vpn_manager.current_proxy,
            "sample": masked_proxies,
            "use_proxies": vpn_manager.use_proxies
        })
    except Exception as e:
        error_logger.error(f"Error getting proxies: {str(e)}")
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route('/api/proxies/reload', methods=['POST'])
def reload_proxies():
    """Reload proxies from the proxies.txt file."""
    try:
        if os.path.exists('proxies.txt'):
            vpn_manager.load_proxies('proxies.txt')
            return jsonify({
                "status": "success",
                "message": f"Reloaded {len(vpn_manager.proxies)} proxies from proxies.txt"
            })
        else:
            return jsonify({
                "status": "error",
                "message": "proxies.txt file not found"
            }), 404
    except Exception as e:
        error_logger.error(f"Error reloading proxies: {str(e)}")
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route('/api/proxies/test', methods=['POST'])
def test_proxy():
    """Test a specific proxy or get a random one and test it."""
    try:
        data = request.json or {}
        proxy = data.get('proxy')
        
        if not proxy:
            # Get a random proxy
            proxy = vpn_manager.get_random_proxy()
            if not proxy:
                return jsonify({
                    "status": "error",
                    "message": "No proxies available to test"
                }), 400
        
        # Set the proxy as current
        vpn_manager.current_proxy = proxy
        
        # Test proxy by checking IP
        start_time = time.time()
        ip = vpn_manager.get_current_ip()
        response_time = time.time() - start_time
        
        return jsonify({
            "status": "success",
            "proxy": proxy,
            "ip": ip,
            "response_time": round(response_time, 2)
        })
    except Exception as e:
        error_logger.error(f"Error testing proxy: {str(e)}")
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route('/api/proxies/toggle', methods=['POST'])
def toggle_proxies():
    """Toggle proxy usage."""
    try:
        data = request.json or {}
        use_proxies = data.get('use_proxies')
        
        if use_proxies is not None:
            vpn_manager.use_proxies = use_proxies
            return jsonify({
                "status": "success",
                "message": f"{'Enabled' if use_proxies else 'Disabled'} proxy usage",
                "use_proxies": vpn_manager.use_proxies
            })
        else:
            return jsonify({
                "status": "error",
                "message": "use_proxies parameter required"
            }), 400
    except Exception as e:
        error_logger.error(f"Error toggling proxies: {str(e)}")
        return jsonify({"status": "error", "message": str(e)}), 500