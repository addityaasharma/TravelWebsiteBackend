from dotenv import load_dotenv
from functools import wraps
from flask import request, jsonify, g
from models import *
import jwt, os, uuid, datetime
from werkzeug.utils import secure_filename


def middleware(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token = request.cookies.get("user_auth_token")
        if not token:
            return jsonify({"status": "error", "message": "Unauthorized"}), 401

        try:
            decoded = jwt.decode(token, os.getenv("SECRET_KEY"), algorithms=["HS256"])

            user = Admin.query.get(decoded["userID"])
            if not user:
                return jsonify({"status": "error", "message": "User not found"}), 404

            g.user = user

        except jwt.ExpiredSignatureError:
            return jsonify({"status": "error", "message": "Token expired"}), 401

        except jwt.InvalidTokenError:
            return jsonify({"status": "error", "message": "Invalid token"}), 401

        return f(*args, **kwargs)

    return decorated
