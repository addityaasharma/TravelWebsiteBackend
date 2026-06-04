from config.extension import *
from config.settings import BaseConfig
from flask import Flask
from flask_cors import CORS
from flask import request

app = Flask(__name__)
app.config.from_object(BaseConfig)

db.init_app(app)
migrate.init_app(app, db)
jwt.init_app(app)
# socketio.init_app(app)
# cors.init_app(app)
# CORS(app)
@app.after_request
def add_cors_headers(response):
    origin = request.headers.get("Origin")
    if origin:
        response.headers["Access-Control-Allow-Origin"] = origin
        response.headers["Access-Control-Allow-Credentials"] = "true"
        response.headers["Access-Control-Allow-Methods"] = "GET, POST, PUT, DELETE, OPTIONS"
        response.headers["Access-Control-Allow-Headers"] = "Content-Type, Authorization"
    return response
limiter.init_app(app)

from routes.adminRoutes import adminBP
from routes.userRoutes import userBP

app.register_blueprint(adminBP)
app.register_blueprint(userBP)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
