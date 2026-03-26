from functools import wraps
from flask import request, jsonify
from pydantic import ValidationError, BaseModel
from typing import Type

def validate_request(schema: Type[BaseModel]):
    def decorator(f):
        @wraps(f)
        def wrapper(*args, **kwargs):
            try:
                # Pydantic validation
                data = request.get_json()
                if data is None:
                    return jsonify({"error": "Request body must be JSON"}), 400
                
                # Create instance of schema to validate
                schema(**data)
                return f(*args, **kwargs)
            except ValidationError as e:
                return jsonify({
                    "error": "Validation error",
                    "details": e.errors()
                }), 422
            except Exception as e:
                return jsonify({"error": str(e)}), 400
        return wrapper
    return decorator
