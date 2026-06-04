from config.extension import db
from sqlalchemy.dialects.postgresql import JSON


class Admin(db.Model):
    __tablename__ = "admin"
    id = db.Column(db.Integer, primary_key=True)
    fullname = db.Column(db.String(255), nullable=True)
    email = db.Column(db.String(255), nullable=False)
    password = db.Column(db.String(255), nullable=False)
    phoneNumber = db.Column(db.String(20))
    

class Banner(db.Model):
    __tablename__ = "banner"
    id = db.Column(db.Integer, primary_key=True)
    image = db.Column(db.String(255), nullable=False)
    link = db.Column(db.String(255), nullable=False)


class Form(db.Model):
    __tablename__ = "form"
    id = db.Column(db.Integer, primary_key=True)
    package_id = db.Column(db.Integer,db.ForeignKey("package.id"), nullable=False)
    package_details = db.Column(db.Text, nullable=False)
    full_name = db.Column(db.String(255), nullable=False)
    email = db.Column(db.String(255))
    phoneNumber = db.Column(db.String(20), nullable=False)
    message = db.Column(db.String(255))


class Country(db.Model):
    __tablename__ = "country"
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255), nullable=False)
    description = db.Column(db.String(255), nullable=True)
    image = db.Column(db.String(255), nullable=False)
    package_collections = db.relationship(
        "PackageCollection",
        uselist=True,
        back_populates="country",
    )


class PackageCollection(db.Model):
    __tablename__ = "package_collection"
    id = db.Column(db.Integer, primary_key=True)
    country_id = db.Column(db.Integer, db.ForeignKey("country.id"), nullable=True)
    name = db.Column(db.String(255), nullable=False)
    description = db.Column(db.Text)
    image = db.Column(db.String(255), nullable=False)
    country = db.relationship("Country", back_populates="package_collections")
    packages = db.relationship(
        "Package", back_populates="package_collection", cascade="all, delete-orphan"
    )


class Package(db.Model):
    __tablename__ = "package"
    id = db.Column(db.Integer, primary_key=True)
    package_collection_id = db.Column(
        db.Integer,
        db.ForeignKey("package_collection.id", ondelete="cascade"),
        nullable=False,
    )
    name = db.Column(db.String(255), nullable=False)
    description = db.Column(db.Text, nullable=True)
    total_price = db.Column(db.Float, nullable=False)
    discount_price = db.Column(db.Float, nullable=False)
    person = db.Column(db.Integer, default=1)
    image = db.Column(JSON, nullable=True)
    package_collection = db.relationship("PackageCollection", back_populates="packages")
    days = db.relationship(
        "PackageDays",
        uselist=True,
        lazy=True,
        back_populates="package",
        cascade="all, delete-orphan",
    )
    reviews = db.relationship(
        "Review",
        uselist=True,
        lazy=True,
        back_populates="package",
        cascade="all, delete-orphan",
    )


class PackageDays(db.Model):
    __tablename__ = "package_days"
    id = db.Column(db.Integer, primary_key=True)
    package_id = db.Column(
        db.Integer, db.ForeignKey("package.id", ondelete="cascade"), nullable=False
    )
    days = db.Column(db.Integer, nullable=False)
    price = db.Column(db.Float, nullable=False)
    discount_price = db.Column(db.Float, nullable=False)
    package = db.relationship("Package", back_populates="days")
    day_description = db.relationship(
        "DaysDescription",
        uselist=True,
        back_populates="package_days",
        cascade="all, delete-orphan",
    )
    activities = db.relationship(
        "Activities",
        uselist=True,
        back_populates="package_days",
        cascade="all, delete-orphan",
    )


class Activities(db.Model):
    __tablename__ = "activities"
    id = db.Column(db.Integer, primary_key=True)
    package_days_id = db.Column(
        db.Integer, db.ForeignKey("package_days.id", ondelete="cascade"), nullable=False
    )
    day = db.Column(db.Integer, nullable=True)
    description = db.Column(db.String(255), nullable=True)
    package_days = db.relationship("PackageDays", back_populates="activities")


class DaysDescription(db.Model):
    __tablename__ = "days_description"
    id = db.Column(db.Integer, primary_key=True)
    package_days_id = db.Column(
        db.Integer, db.ForeignKey("package_days.id", ondelete="cascade"), nullable=False
    )
    day = db.Column(db.Integer, nullable=True)
    description = db.Column(db.String(255), nullable=True)
    package_days = db.relationship("PackageDays", back_populates="day_description")


class Review(db.Model):
    __tablename__ = "review"
    id = db.Column(db.Integer, primary_key=True)
    package_id = db.Column(
        db.Integer,
        db.ForeignKey("package.id", ondelete="CASCADE"),
        nullable=False,
    )
    name = db.Column(db.String(255), nullable=False)
    star = db.Column(db.Integer, default=5, nullable=False)
    review = db.Column(db.Text)
    package = db.relationship("Package", back_populates="reviews")