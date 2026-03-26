from flask import jsonify, current_app
from werkzeug.exceptions import HTTPException
import logging

def register_error_handlers(app):
    @app.errorhandler(Exception)
    def handle_exception(e):
        # Pass through HTTP exceptions
        if isinstance(e, HTTPException):
            return jsonify({
                "error": e.name,
                "message": e.description,
                "code": e.code
            }), e.code

        # Log non-HTTP exceptions
        current_app.logger.error(f"Unhandled Exception: {str(e)}", exc_info=True)

        return jsonify({
            "error": "Internal Server Error",
            "message": "An unexpected error occurred. Please try again later.",
            "code": 500
        }), 500

    @app.errorhandler(404)
    def handle_not_found(e):
        return jsonify({
            "error": "Not Found",
            "message": "The requested resource was not found.",
            "code": 404
        }), 404

    @app.errorhandler(403)
    def handle_forbidden(e):
        return jsonify({
            "error": "Forbidden",
            "message": "You don't have permission to perform this action.",
            "code": 403
        }), 403
