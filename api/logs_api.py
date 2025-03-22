import os
from flask import request, jsonify
from app import app

# Get loggers
activity_logger = logging.getLogger("activity")
error_logger = logging.getLogger("error")

@app.route('/api/logs/activity', methods=['GET'])
def get_activity_logs():
    """Get activity logs."""
    try:
        lines = request.args.get('lines', 100, type=int)
        
        with open(os.getenv('ACTIVITY_LOG', 'logs/bot_activity.log'), 'r') as f:
            logs = f.readlines()
        
        # Get the most recent lines
        logs = logs[-lines:] if len(logs) > lines else logs
        
        return jsonify({
            "status": "success",
            "logs": logs
        })
    except Exception as e:
        error_logger.error(f"Error getting activity logs: {str(e)}")
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route('/api/logs/error', methods=['GET'])
def get_error_logs():
    """Get error logs."""
    try:
        lines = request.args.get('lines', 100, type=int)
        
        with open(os.getenv('ERROR_LOG', 'logs/bot_errors.log'), 'r') as f:
            logs = f.readlines()
        
        # Get the most recent lines
        logs = logs[-lines:] if len(logs) > lines else logs
        
        return jsonify({
            "status": "success",
            "logs": logs
        })
    except Exception as e:
        error_logger.error(f"Error getting error logs: {str(e)}")
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route('/api/logs/clear', methods=['POST'])
def clear_logs():
    """Clear log files."""
    try:
        data = request.json or {}
        log_type = data.get('type', 'all')
        
        if log_type in ['activity', 'all']:
            with open(os.getenv('ACTIVITY_LOG', 'logs/bot_activity.log'), 'w') as f:
                f.write('')
        
        if log_type in ['error', 'all']:
            with open(os.getenv('ERROR_LOG', 'logs/bot_errors.log'), 'w') as f:
                f.write('')
        
        return jsonify({
            "status": "success",
            "message": f"Cleared {log_type} logs"
        })
    except Exception as e:
        error_logger.error(f"Error clearing logs: {str(e)}")
        return jsonify({"status": "error", "message": str(e)}), 500