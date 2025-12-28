from quart import request, jsonify
from functools import wraps

API_KEY = ""

def require_api_key(f):
    """Decorator to require API key authentication for endpoints"""
    @wraps(f)
    async def decorated_function(*args, **kwargs):
        api_key = request.args.get('api_key')
        
        if not api_key:
            return jsonify({"error": "API key is required"}), 401
        
        if api_key != API_KEY:
            return jsonify({"error": "Invalid API key"}), 403
        
        return await f(*args, **kwargs)
    
    return decorated_function
