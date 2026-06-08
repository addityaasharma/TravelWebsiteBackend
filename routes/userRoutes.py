from flask import request, jsonify, g, Blueprint
from config.extension import *
from models import *
import json

userBP = Blueprint("user", __name__, url_prefix="/user")
limiter.limit("100 per hour")(userBP)


@userBP.route("/countries", methods=["GET"])
def get_countries():
    try:
        countries = Country.query.all()
        return (
            jsonify(
                {
                    "status": "success",
                    "data": [
                        {
                            "id": c.id,
                            "name": c.name,
                            "description": c.description,
                            "image": c.image,
                            "total_collections": len(c.package_collections),
                        }
                        for c in countries
                    ],
                }
            ),
            200,
        )
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500


@userBP.route("/countries/<int:country_id>", methods=["GET"])
def get_country(country_id):
    try:
        country = Country.query.get(country_id)
        if not country:
            return jsonify({"status": "error", "message": "Country not found"}), 404

        return (
            jsonify(
                {
                    "status": "success",
                    "data": {
                        "id": country.id,
                        "name": country.name,
                        "description": country.description,
                        "image": country.image,
                        "package_collections": [
                            {
                                "id": c.id,
                                "name": c.name,
                                "description": c.description,
                                "image": c.image,
                                "total_packages": len(c.packages),
                                "packages": [
                                    {
                                        "id": p.id,
                                        "name": p.name,
                                        "description": p.description,
                                        "total_price": p.total_price,
                                        "discount_price": p.discount_price,
                                        "person": p.person,
                                        "image": p.image,
                                        "total_days": len(p.days),
                                        "average_rating": (
                                            round(
                                                sum(r.star for r in p.reviews)
                                                / len(p.reviews),
                                                1,
                                            )
                                            if p.reviews
                                            else 0
                                        ),
                                        "total_reviews": len(p.reviews),
                                    }
                                    for p in c.packages
                                ],
                            }
                            for c in country.package_collections
                        ],
                    },
                }
            ),
            200,
        )
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500


@userBP.route("/collections", methods=["GET"])
def get_collections():
    try:
        collections = PackageCollection.query.all()
        return (
            jsonify(
                {
                    "status": "success",
                    "data": [
                        {
                            "id": c.id,
                            "name": c.name,
                            "description": c.description,
                            "image": c.image,
                            "country_id": c.country_id,
                            "total_packages": len(c.packages),
                            "packages": [
                                {
                                    "id": p.id,
                                    "name": p.name,
                                    "description": p.description,
                                    "total_price": p.total_price,
                                    "discount_price": p.discount_price,
                                    "person": p.person,
                                    "image": p.image,
                                    "total_days": len(p.days),
                                    "average_rating": (
                                        round(
                                            sum(r.star for r in p.reviews)
                                            / len(p.reviews),
                                            1,
                                        )
                                        if p.reviews
                                        else 0
                                    ),
                                    "total_reviews": len(p.reviews),
                                }
                                for p in c.packages
                            ],
                        }
                        for c in collections
                    ],
                }
            ),
            200,
        )
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500


@userBP.route("/collections/<int:collection_id>", methods=["GET"])
def get_collection(collection_id):
    try:
        collection = PackageCollection.query.get(collection_id)
        if not collection:
            return jsonify({"status": "error", "message": "Collection not found"}), 404

        return (
            jsonify(
                {
                    "status": "success",
                    "data": {
                        "id": collection.id,
                        "name": collection.name,
                        "description": collection.description,
                        "image": collection.image,
                        "country_id": collection.country_id,
                        "packages": [
                            {
                                "id": p.id,
                                "name": p.name,
                                "description": p.description,
                                "total_price": p.total_price,
                                "discount_price": p.discount_price,
                                "person": p.person,
                                "image": p.image,
                                "average_rating": (
                                    round(
                                        sum(r.star for r in p.reviews) / len(p.reviews),
                                        1,
                                    )
                                    if p.reviews
                                    else 0
                                ),
                                "total_reviews": len(p.reviews),
                                "days": [
                                    {
                                        "id": d.id,
                                        "days": d.days,
                                        "price": d.price,
                                        "discount_price": d.discount_price,
                                    }
                                    for d in p.days
                                ],
                            }
                            for p in collection.packages
                        ],
                    },
                }
            ),
            200,
        )
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500


# ── FIXED: filter by country using association table ──────────────────────────
@userBP.route("/packages", methods=["GET"])
def get_packages():
    try:
        country_id = request.args.get("country_id", type=int)
        min_price = request.args.get("min_price", type=float)
        max_price = request.args.get("max_price", type=float)
        person = request.args.get("person", type=int)
        sort = request.args.get("sort", "latest")
        page = request.args.get("page", 1, type=int)
        per_page = request.args.get("per_page", 10, type=int)

        query = Package.query

        if country_id:
            # Join through association table → PackageCollection → Country
            query = (
                query.join(
                    package_collection_association,
                    Package.id == package_collection_association.c.package_id,
                )
                .join(
                    PackageCollection,
                    PackageCollection.id
                    == package_collection_association.c.package_collection_id,
                )
                .filter(PackageCollection.country_id == country_id)
                .distinct()
            )

        if min_price:
            query = query.filter(Package.discount_price >= min_price)
        if max_price:
            query = query.filter(Package.discount_price <= max_price)
        if person:
            query = query.filter(Package.person >= person)

        if sort == "price_asc":
            query = query.order_by(Package.discount_price.asc())
        elif sort == "price_desc":
            query = query.order_by(Package.discount_price.desc())
        else:
            query = query.order_by(Package.id.desc())

        paginated = query.paginate(page=page, per_page=per_page, error_out=False)

        return (
            jsonify(
                {
                    "status": "success",
                    "pagination": {
                        "page": paginated.page,
                        "per_page": paginated.per_page,
                        "total": paginated.total,
                        "pages": paginated.pages,
                        "has_next": paginated.has_next,
                        "has_prev": paginated.has_prev,
                    },
                    "data": [
                        {
                            "id": p.id,
                            "name": p.name,
                            "description": p.description,
                            "total_price": p.total_price,
                            "discount_price": p.discount_price,
                            "person": p.person,
                            "image": p.image,
                            # FIXED: replaced package_collection_id with collections list
                            "collections": [
                                {"id": c.id, "name": c.name} for c in p.collections
                            ],
                            "average_rating": (
                                round(
                                    sum(r.star for r in p.reviews) / len(p.reviews), 1
                                )
                                if p.reviews
                                else 0
                            ),
                            "total_reviews": len(p.reviews),
                            "total_days": len(p.days),
                        }
                        for p in paginated.items
                    ],
                }
            ),
            200,
        )
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500


@userBP.route("/packages/<int:package_id>", methods=["GET"])
def get_package(package_id):
    try:
        package = Package.query.get(package_id)
        if not package:
            return jsonify({"status": "error", "message": "Package not found"}), 404

        return (
            jsonify(
                {
                    "status": "success",
                    "data": {
                        "id": package.id,
                        "name": package.name,
                        "description": package.description,
                        "total_price": package.total_price,
                        "discount_price": package.discount_price,
                        "person": package.person,
                        "image": package.image,
                        # FIXED: replaced package_collection_id with collections list
                        "collections": [
                            {"id": c.id, "name": c.name} for c in package.collections
                        ],
                        "average_rating": (
                            round(
                                sum(r.star for r in package.reviews)
                                / len(package.reviews),
                                1,
                            )
                            if package.reviews
                            else 0
                        ),
                        "reviews": [
                            {
                                "id": r.id,
                                "name": r.name,
                                "star": r.star,
                                "review": r.review,
                            }
                            for r in package.reviews
                        ],
                        "days": [
                            {
                                "id": d.id,
                                "days": d.days,
                                "price": d.price,
                                "discount_price": d.discount_price,
                                "activities": [
                                    {
                                        "id": a.id,
                                        "day": a.day,
                                        "description": a.description,
                                    }
                                    for a in d.activities
                                ],
                                "day_description": [
                                    {
                                        "id": dd.id,
                                        "day": dd.day,
                                        "description": dd.description,
                                    }
                                    for dd in d.day_description
                                ],
                            }
                            for d in package.days
                        ],
                    },
                }
            ),
            200,
        )
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500


@userBP.route("/packages/<int:package_id>/review", methods=["POST"])
def add_review(package_id):
    try:
        package = Package.query.get(package_id)
        if not package:
            return jsonify({"status": "error", "message": "Package not found"}), 404

        data = request.get_json()
        name = data.get("name")
        star = data.get("star")
        review_text = data.get("review")

        if not name:
            return jsonify({"status": "error", "message": "Name is required"}), 400
        if star is None:
            return (
                jsonify({"status": "error", "message": "Star rating is required"}),
                400,
            )
        if not isinstance(star, int) or star < 1 or star > 5:
            return (
                jsonify(
                    {
                        "status": "error",
                        "message": "Star must be an integer between 1 and 5",
                    }
                ),
                400,
            )

        review = Review(package_id=package_id, name=name, star=star, review=review_text)
        db.session.add(review)
        db.session.commit()

        return (
            jsonify(
                {
                    "status": "success",
                    "message": "Review submitted successfully",
                    "data": {
                        "id": review.id,
                        "name": review.name,
                        "star": review.star,
                        "review": review.review,
                    },
                }
            ),
            201,
        )
    except Exception as e:
        db.session.rollback()
        return jsonify({"status": "error", "message": str(e)}), 500


# ── FIXED: removed package.package_collection reference ──────────────────────
@userBP.route("/packages/<int:package_id>/enquiry", methods=["POST"])
def submit_enquiry(package_id):
    try:
        package = Package.query.get(package_id)
        if not package:
            return jsonify({"status": "error", "message": "Package not found"}), 404

        data = request.get_json()
        full_name = data.get("full_name")
        email = data.get("email")
        phoneNumber = data.get("phoneNumber")
        enquiry_type = data.get("enquiry_type")
        message = data.get("message")

        if not full_name:
            return jsonify({"status": "error", "message": "Full name is required"}), 400
        if not phoneNumber:
            return (
                jsonify({"status": "error", "message": "Phone number is required"}),
                400,
            )

        # FIXED: use package.collections (list) instead of package.package_collection
        collection_names = (
            ", ".join(c.name for c in package.collections)
            if package.collections
            else None
        )

        package_details = {
            "name": package.name,
            "total_price": package.total_price,
            "discount_price": package.discount_price,
            "person": package.person,
            "collections": collection_names,
        }

        form = Form(
            package_id=package_id,
            package_details=json.dumps(package_details),
            full_name=full_name,
            email=email,
            phoneNumber=phoneNumber,
            enquiry_type=enquiry_type,
            message=message,
        )
        db.session.add(form)
        db.session.commit()

        return (
            jsonify(
                {
                    "status": "success",
                    "message": "Enquiry submitted successfully. We will contact you soon.",
                    "data": {
                        "id": form.id,
                        "full_name": form.full_name,
                        "email": form.email,
                        "phoneNumber": form.phoneNumber,
                        "message": form.message,
                        "package_details": package_details,
                    },
                }
            ),
            201,
        )
    except Exception as e:
        db.session.rollback()
        return jsonify({"status": "error", "message": str(e)}), 500


@userBP.route("/packages/<int:package_id>/reviews", methods=["GET"])
def get_package_reviews(package_id):
    try:
        package = Package.query.get(package_id)
        if not package:
            return jsonify({"status": "error", "message": "Package not found"}), 404

        page = request.args.get("page", 1, type=int)
        per_page = request.args.get("per_page", 10, type=int)
        star = request.args.get("star", type=int)

        query = Review.query.filter_by(package_id=package_id)
        if star:
            if star < 1 or star > 5:
                return (
                    jsonify(
                        {"status": "error", "message": "Star must be between 1 and 5"}
                    ),
                    400,
                )
            query = query.filter(Review.star == star)

        query = query.order_by(Review.id.desc())
        paginated = query.paginate(page=page, per_page=per_page, error_out=False)

        return (
            jsonify(
                {
                    "status": "success",
                    "summary": {
                        "total_reviews": len(package.reviews),
                        "average_rating": (
                            round(
                                sum(r.star for r in package.reviews)
                                / len(package.reviews),
                                1,
                            )
                            if package.reviews
                            else 0
                        ),
                        "star_distribution": {
                            str(s): sum(1 for r in package.reviews if r.star == s)
                            for s in range(1, 6)
                        },
                    },
                    "pagination": {
                        "page": paginated.page,
                        "per_page": paginated.per_page,
                        "total": paginated.total,
                        "pages": paginated.pages,
                        "has_next": paginated.has_next,
                        "has_prev": paginated.has_prev,
                    },
                    "data": [
                        {"id": r.id, "name": r.name, "star": r.star, "review": r.review}
                        for r in paginated.items
                    ],
                }
            ),
            200,
        )
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500


@userBP.route("/banners", methods=["GET"])
def get_banners_public():
    try:
        banners = Banner.query.all()
        return (
            jsonify(
                {
                    "status": "success",
                    "data": [
                        {"id": b.id, "image": b.image, "link": b.link} for b in banners
                    ],
                }
            ),
            200,
        )
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500


@userBP.route("/home", methods=["GET"])
def home():
    try:
        collections = (
            PackageCollection.query.filter_by(show_on_home=True)
            .order_by(PackageCollection.home_index)
            .all()
        )

        result = []
        for collection in collections:
            packages_data = []
            for pkg in collection.packages[:6]:
                avg_rating = (
                    round(sum(r.star for r in pkg.reviews) / len(pkg.reviews), 1)
                    if pkg.reviews
                    else 0
                )
                packages_data.append(
                    {
                        "id": pkg.id,
                        "name": pkg.name,
                        "description": pkg.description,
                        "total_price": pkg.total_price,
                        "discount_price": pkg.discount_price,
                        "person": pkg.person,
                        "image": pkg.image,
                        "average_rating": avg_rating,
                        "total_reviews": len(pkg.reviews),
                        "days": [
                            {
                                "id": d.id,
                                "days": d.days,
                                "price": d.price,
                                "discount_price": d.discount_price,
                            }
                            for d in pkg.days
                        ],
                    }
                )

            result.append(
                {
                    "id": collection.id,
                    "name": collection.name,
                    "description": collection.description,
                    "image": collection.image,
                    "country_id": collection.country_id,
                    "home_index": collection.home_index,
                    "total_packages": len(collection.packages),
                    "packages": packages_data,
                }
            )

        return jsonify({"status": "success", "data": result}), 200
    except Exception as e:
        return (
            jsonify(
                {"status": "error", "message": "Failed to fetch home", "error": str(e)}
            ),
            500,
        )


# ── FIXED: suggested packages — uses collections (many-to-many) ───────────────
@userBP.route("/packages/<int:package_id>/suggested", methods=["GET"])
def get_suggested_packages(package_id):
    try:
        package = Package.query.get(package_id)
        if not package:
            return jsonify({"status": "error", "message": "Package not found"}), 404

        suggested = []
        suggested_ids = set()

        # 1. Same collections, excluding current package
        for collection in package.collections:
            same_collection_pkgs = [
                p
                for p in collection.packages
                if p.id != package_id and p.id not in suggested_ids
            ]
            for p in same_collection_pkgs:
                suggested_ids.add(p.id)
                suggested.append(p)
            if len(suggested) >= 16:
                break

        # 2. Same country via any collection, excluding already added
        if len(suggested) < 16:
            country_ids = {c.country_id for c in package.collections if c.country_id}
            if country_ids:
                same_country = (
                    Package.query.join(
                        package_collection_association,
                        Package.id == package_collection_association.c.package_id,
                    )
                    .join(
                        PackageCollection,
                        PackageCollection.id
                        == package_collection_association.c.package_collection_id,
                    )
                    .filter(
                        PackageCollection.country_id.in_(country_ids),
                        Package.id != package_id,
                        Package.id.notin_(suggested_ids),
                    )
                    .distinct()
                    .limit(16 - len(suggested))
                    .all()
                )
                for p in same_country:
                    suggested_ids.add(p.id)
                suggested.extend(same_country)

        # 3. Fill remainder with any other packages
        if len(suggested) < 16:
            others = (
                Package.query.filter(
                    Package.id != package_id, Package.id.notin_(suggested_ids)
                )
                .limit(16 - len(suggested))
                .all()
            )
            suggested.extend(others)

        def fmt(p):
            avg = (
                round(sum(r.star for r in p.reviews) / len(p.reviews), 1)
                if p.reviews
                else 0
            )
            return {
                "id": p.id,
                "name": p.name,
                "description": p.description,
                "total_price": p.total_price,
                "discount_price": p.discount_price,
                "person": p.person,
                "image": p.image,
                "average_rating": avg,
                "total_reviews": len(p.reviews),
                # FIXED: replaced package_collection_id with collections list
                "collections": [{"id": c.id, "name": c.name} for c in p.collections],
                "days": [
                    {
                        "id": d.id,
                        "days": d.days,
                        "price": d.price,
                        "discount_price": d.discount_price,
                    }
                    for d in p.days
                ],
            }

        return (
            jsonify({"status": "success", "data": [fmt(p) for p in suggested[:16]]}),
            200,
        )
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500
