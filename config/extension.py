from flask_sqlalchemy import SQLAlchemy
# from flask_socketio import SocketIO
from flask_migrate import Migrate
from flask_jwt_extended import JWTManager
from flask_cors import CORS
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
# import redis, os, resend, boto3
from dotenv import load_dotenv
import cloudinary
import cloudinary.uploader
import os

# from celery import Celery
# import razorpay
# import hmac
# import hashlib
# import uuid

load_dotenv()

db = SQLAlchemy()
# socketio = SocketIO()
migrate = Migrate()
jwt = JWTManager()
cors = CORS(resources={r"/*": {"origins": "*"}})
limiter = Limiter(
    key_func=get_remote_address, default_limits=["200 per day", "50 per hour"]
)
cloudinary.config(
    cloud_name=os.environ.get("CLOUDINARY_CLOUD_NAME"),
    api_key=os.environ.get("CLOUDINARY_API_KEY"),
    api_secret=os.environ.get("CLOUDINARY_API_SECRET"),
)
# redis = redis.Redis.from_url(os.getenv("REDIS_URL"), decode_responses=True)
# resend.api_key = os.getenv("RESEND_API_KEY")
# celery = Celery("tasks", broker=os.getenv("REDIS_URL"), backend=os.getenv("REDIS_URL"))
# razorpay_client = razorpay.Client(
#     auth=(os.getenv("RAZORPAY_KEY_ID"), os.getenv("RAZORPAY_KEY_SECRET"))
# )
