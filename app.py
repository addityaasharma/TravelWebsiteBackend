from config.extension import *
from config.settings import BaseConfig
from flask import Flask
from flask_cors import CORS

app = Flask(__name__)
app.config.from_object(BaseConfig)

db.init_app(app)
migrate.init_app(app, db)
jwt.init_app(app)
# socketio.init_app(app)
# cors.init_app(app)
CORS(app)
limiter.init_app(app)

from routes.adminRoutes import adminBP
from routes.userRoutes import userBP

app.register_blueprint(adminBP)
app.register_blueprint(userBP)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
