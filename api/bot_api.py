import os
from flask import request, jsonify
from app import app, traffic_bot

# Get loggers
activity_logger = logging.getLogger("activity")
error_logger = logging.getLogger("error")

@app.route('/api/bot/start', methods=['POST'])
def start_bot():
    """Start the traffic bot."""
    try:
        data = request.json or {}
        num_workers = int(data.get('workers', os.getenv('DEFAULT_WORKERS', 8)))
        max_workers = int(os.getenv('MAX_WORKERS', 12))
        
        # Cap workers at the maximum allowed
        if num_workers > max_workers:
            num_workers = max_workers
        
        # Load keywords and URLs if provided
        if 'keywords' in data:
            traffic_bot.keywords = data['keywords']
            activity_logger.info(f"Loaded {len(traffic_bot.keywords)} keywords from request")
        
        if 'urls' in data:
            traffic_bot.urls = data['urls']
            activity_logger.info(f"Loaded {len(traffic_bot.urls)} URLs from request")
        
        # Start bot if not already running
        if not traffic_bot.running:
            traffic_bot.start(num_workers)
            return jsonify({
                "status": "success", 
                "message": f"Started bot with {num_workers} workers"
            })
        else:
            return jsonify({
                "status": "warning", 
                "message": "Bot is already running"
            })
    except Exception as e:
        error_logger.error(f"Error starting bot: {str(e)}")
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route('/api/bot/stop', methods=['POST'])
def stop_bot():
    """Stop the traffic bot."""
    try:
        if traffic_bot.running:
            traffic_bot.stop()
            return jsonify({
                "status": "success", 
                "message": "Stopped bot"
            })
        else:
            return jsonify({
                "status": "warning", 
                "message": "Bot is not running"
            })
    except Exception as e:
        error_logger.error(f"Error stopping bot: {str(e)}")
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route('/api/bot/pause', methods=['POST'])
def pause_bot():
    """Pause the traffic bot."""
    try:
        if traffic_bot.running and not traffic_bot.paused:
            traffic_bot.pause()
            return jsonify({
                "status": "success", 
                "message": "Paused bot"
            })
        else:
            return jsonify({
                "status": "warning", 
                "message": "Bot is not running or already paused"
            })
    except Exception as e:
        error_logger.error(f"Error pausing bot: {str(e)}")
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route('/api/bot/resume', methods=['POST'])
def resume_bot():
    """Resume the traffic bot after pausing."""
    try:
        if traffic_bot.running and traffic_bot.paused:
            traffic_bot.resume()
            return jsonify({
                "status": "success", 
                "message": "Resumed bot"
            })
        else:
            return jsonify({
                "status": "warning", 
                "message": "Bot is not running or not paused"
            })
    except Exception as e:
        error_logger.error(f"Error resuming bot: {str(e)}")
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route('/api/bot/stats', methods=['GET'])
def get_bot_stats():
    """Get bot statistics."""
    try:
        stats = traffic_bot.get_stats()
        return jsonify({
            "status": "success",
            "stats": stats
        })
    except Exception as e:
        error_logger.error(f"Error getting bot stats: {str(e)}")
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route('/api/bot/keywords', methods=['POST'])
def update_keywords():
    """Update the bot's keywords."""
    try:
        data = request.json
        if not data or 'keywords' not in data:
            return jsonify({
                "status": "error", 
                "message": "No keywords provided"
            }), 400
        
        traffic_bot.keywords = data['keywords']
        
        return jsonify({
            "status": "success",
            "message": f"Updated with {len(traffic_bot.keywords)} keywords"
        })
    except Exception as e:
        error_logger.error(f"Error updating keywords: {str(e)}")
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route('/api/bot/urls', methods=['POST'])
def update_urls():
    """Update the bot's URLs."""
    try:
        data = request.json
        if not data or 'urls' not in data:
            return jsonify({
                "status": "error", 
                "message": "No URLs provided"
            }), 400
        
        traffic_bot.urls = data['urls']
        
        return jsonify({
            "status": "success",
            "message": f"Updated with {len(traffic_bot.urls)} URLs"
        })
    except Exception as e:
        error_logger.error(f"Error updating URLs: {str(e)}")
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route('/api/bot/tracking', methods=['GET'])
def get_tracking_urls():
    """Get custom tracking URLs."""
    try:
        return jsonify({
            "status": "success",
            "tracking_urls": traffic_bot.custom_tracking_urls
        })
    except Exception as e:
        error_logger.error(f"Error getting tracking URLs: {str(e)}")
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route('/api/bot/tracking', methods=['POST'])
def add_tracking_url():
    """Add a custom tracking URL."""
    try:
        data = request.json
        if not data or 'original_url' not in data or 'tracking_url' not in data:
            return jsonify({
                "status": "error", 
                "message": "Original URL and tracking URL are required"
            }), 400
        
        traffic_bot.add_tracking_url(data['original_url'], data['tracking_url'])
        
        return jsonify({
            "status": "success",
            "message": f"Added tracking URL for {data['original_url']}"
        })
    except Exception as e:
        error_logger.error(f"Error adding tracking URL: {str(e)}")
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route('/api/bot/tracking/<path:original_url>', methods=['DELETE'])
def remove_tracking_url(original_url):
    """Remove a custom tracking URL."""
    try:
        if original_url in traffic_bot.custom_tracking_urls:
            del traffic_bot.custom_tracking_urls[original_url]
            return jsonify({
                "status": "success",
                "message": f"Removed tracking URL for {original_url}"
            })
        else:
            return jsonify({
                "status": "warning",
                "message": f"No tracking URL found for {original_url}"
            })
    except Exception as e:
        error_logger.error(f"Error removing tracking URL: {str(e)}")
        return jsonify({"status": "error", "message": str(e)}), 500