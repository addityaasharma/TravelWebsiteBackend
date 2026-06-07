from models import *
from flask import request, jsonify, g, Blueprint
from config.middleware import middleware
from config.function import *
from werkzeug.security import check_password_hash, generate_password_hash
from dotenv import load_dotenv
import jwt, os, datetime, json
from datetime import timedelta

load_dotenv()

adminBP = Blueprint("admin", __name__, url_prefix="/admin")

SECRET_KEY = os.getenv("SECRET_KEY")


@adminBP.route("/signup", methods=["POST"])
def signup():
    try:
        data = request.get_json()

        fullname = data.get("fullname")
        email = data.get("email")
        password = data.get("password")
        phoneNumber = data.get("phoneNumber")

        if not email or not password:
            return (
                jsonify(
                    {"status": "error", "message": "Email and password are required"}
                ),
                400,
            )

        existing_admin = Admin.query.filter_by(email=email).first()
        if existing_admin:
            return (
                jsonify(
                    {
                        "status": "error",
                        "message": "Admin with this email already exists",
                    }
                ),
                409,
            )

        hashed_password = generate_password_hash(password)

        new_admin = Admin(
            fullname=fullname,
            email=email,
            password=hashed_password,
            phoneNumber=phoneNumber,
        )

        db.session.add(new_admin)
        db.session.commit()

        token = jwt.encode(
            {
                "userID": new_admin.id,
                "exp": datetime.datetime.utcnow() + datetime.timedelta(days=7),
            },
            SECRET_KEY,
            algorithm="HS256",
        )

        response = jsonify(
            {
                "status": "success",
                "message": "Admin created successfully",
                "admin": {
                    "id": new_admin.id,
                    "fullname": new_admin.fullname,
                    "email": new_admin.email,
                },
            }
        )

        response.set_cookie(
            "user_auth_token",
            token,
            httponly=True,
            secure=False,
            samesite="Lax",
            max_age=7 * 24 * 60 * 60,
        )

        return response, 201

    except Exception as e:
        db.session.rollback()
        return jsonify({"status": "error", "message": "Failed to signup"}), 500


@adminBP.route("/login", methods=["POST"])
def login():
    try:
        data = request.get_json()
        email = data.get("email")
        password = data.get("password")
        if not email or not password:
            return (
                jsonify(
                    {"status": "error", "message": "Email and password are required"}
                ),
                400,
            )

        admin = Admin.query.filter_by(email=email).first()
        if not admin:
            return (
                jsonify({"status": "error", "message": "Invalid email or password"}),
                401,
            )

        if not check_password_hash(admin.password, password):
            return (
                jsonify({"status": "error", "message": "Invalid email or password"}),
                401,
            )

        token = jwt.encode(
            {
                "userID": admin.id,
                "exp": datetime.datetime.utcnow() + datetime.timedelta(days=7),
            },
            SECRET_KEY,
            algorithm="HS256",
        )

        response = jsonify(
            {
                "status": "success",
                "message": "Login successful",
                "admin": {
                    "id": admin.id,
                    "fullname": admin.fullname,
                    "email": admin.email,
                },
            }
        )

        response.set_cookie(
            "user_auth_token",
            token,
            httponly=True,
            secure=False,
            samesite="Lax",
            max_age=7 * 24 * 60 * 60,
        )

        return response, 200

    except Exception as e:
        return jsonify({"status": "error", "message": "Failed to login"}), 500


@adminBP.route("/logout", methods=["POST"])
@middleware
def logout():
    try:
        response = jsonify({"status": "success", "message": "Logged out successfully"})
        response.delete_cookie(
            "user_auth_token",
            httponly=True,
            secure=False,
            samesite="Lax",
        )
        return response, 200

    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500


@adminBP.route("/", methods=["GET"])
@middleware
def get_admin():
    try:
        admin = Admin.query.get(g.user.id)
        if not admin:
            return jsonify({"status": "error", "message": "Admin not found"}), 404

        return (
            jsonify(
                {
                    "status": "success",
                    "data": {
                        "id": admin.id,
                        "fullname": admin.fullname,
                        "email": admin.email,
                        "phoneNumber": admin.phoneNumber,
                    },
                }
            ),
            200,
        )

    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500


# UPDATE admin details
@adminBP.route("/", methods=["PUT"])
@middleware
def update_admin():
    try:
        admin = Admin.query.get(g.user.id)
        if not admin:
            return jsonify({"status": "error", "message": "Admin not found"}), 404

        data = request.get_json()
        fullname = data.get("fullname")
        email = data.get("email")
        phoneNumber = data.get("phoneNumber")
        old_password = data.get("old_password")
        new_password = data.get("new_password")

        if fullname:
            admin.fullname = fullname

        if phoneNumber:
            admin.phoneNumber = phoneNumber

        if email:
            existing = Admin.query.filter_by(email=email).first()
            if existing and existing.id != admin.id:
                return (
                    jsonify({"status": "error", "message": "Email already in use"}),
                    400,
                )
            admin.email = email

        # --- Password change (optional) ---
        if old_password or new_password:
            if not old_password or not new_password:
                return (
                    jsonify(
                        {
                            "status": "error",
                            "message": "Both old and new password are required",
                        }
                    ),
                    400,
                )

            from werkzeug.security import check_password_hash, generate_password_hash

            if not check_password_hash(admin.password, old_password):
                return (
                    jsonify(
                        {"status": "error", "message": "Old password is incorrect"}
                    ),
                    400,
                )

            admin.password = generate_password_hash(new_password)

        db.session.commit()

        return (
            jsonify(
                {
                    "status": "success",
                    "message": "Admin details updated successfully",
                    "data": {
                        "id": admin.id,
                        "fullname": admin.fullname,
                        "email": admin.email,
                        "phoneNumber": admin.phoneNumber,
                    },
                }
            ),
            200,
        )

    except Exception as e:
        db.session.rollback()
        return jsonify({"status": "error", "message": str(e)}), 500


@adminBP.route("/country", methods=["GET"])
@middleware
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
                        }
                        for c in countries
                    ],
                }
            ),
            200,
        )

    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500


@adminBP.route("/country", methods=["POST"])
@middleware
def create_country():
    try:
        name = request.form.get("name")
        description = request.form.get("description")
        image_file = request.files.get("image")

        if not name:
            return jsonify({"status": "error", "message": "Name is required"}), 400

        if not image_file:
            return jsonify({"status": "error", "message": "Image is required"}), 400

        uploaded, error = upload_images(image_file, folder="countries")
        if error:
            return jsonify({"status": "error", "message": error}), 400

        country = Country(
            name=name,
            description=description,
            image=uploaded[0]["url"],
        )
        db.session.add(country)
        db.session.flush()  # get country.id before committing

        collection_names = request.form.getlist("collection_names[]")
        collection_descriptions = request.form.getlist("collection_descriptions[]")
        collection_show_on_home = request.form.getlist("collection_show_on_home[]")
        collection_home_indexes = request.form.getlist("collection_home_indexes[]")
        collection_image_files = request.files.getlist("collection_images[]")

        created_collections = []
        for i, col_name in enumerate(collection_names):
            if not col_name.strip():
                continue

            col_image_url = None
            if i < len(collection_image_files) and collection_image_files[i].filename:
                col_uploaded, col_error = upload_images(
                    collection_image_files[i], folder="package-collections"
                )
                if col_error:
                    db.session.rollback()
                    return (
                        jsonify(
                            {
                                "status": "error",
                                "message": f"Collection image error: {col_error}",
                            }
                        ),
                        400,
                    )
                col_image_url = col_uploaded[0]["url"]

            show_home = (
                collection_show_on_home[i].lower() == "true"
                if i < len(collection_show_on_home)
                else False
            )
            try:
                home_idx = (
                    int(collection_home_indexes[i])
                    if i < len(collection_home_indexes)
                    else 0
                )
            except (ValueError, TypeError):
                home_idx = 0

            col = PackageCollection(
                country_id=country.id,
                name=col_name.strip(),
                description=(
                    collection_descriptions[i].strip()
                    if i < len(collection_descriptions)
                    else ""
                ),
                image=col_image_url or "",
                show_on_home=show_home,
                home_index=home_idx,
            )
            db.session.add(col)
            created_collections.append(col)

        db.session.commit()

        return (
            jsonify(
                {
                    "status": "success",
                    "message": "Country created successfully",
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
                                "show_on_home": c.show_on_home,
                                "home_index": c.home_index,
                            }
                            for c in created_collections
                        ],
                    },
                }
            ),
            201,
        )

    except Exception as e:
        db.session.rollback()
        return jsonify({"status": "error", "message": str(e)}), 500


@adminBP.route("/country/<int:country_id>", methods=["GET"])
@middleware
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
                                "show_on_home": c.show_on_home,
                                "home_index": c.home_index,
                                "total_packages": len(c.packages),
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


@adminBP.route("/country/<int:country_id>", methods=["PUT"])
@middleware
def edit_country(country_id):
    try:
        country = Country.query.get(country_id)
        if not country:
            return jsonify({"status": "error", "message": "Country not found"}), 404

        name = request.form.get("name")
        description = request.form.get("description")
        image_file = request.files.get("image")

        if name:
            country.name = name
        if description is not None:
            country.description = description
        if image_file:
            if country.image:
                public_id = "/".join(country.image.split("/")[-2:]).rsplit(".", 1)[0]
                delete_images({"public_id": public_id})
            uploaded, error = upload_images(image_file, folder="countries")
            if error:
                return jsonify({"status": "error", "message": error}), 400
            country.image = uploaded[0]["url"]

        new_names = request.form.getlist("new_collection_names[]")
        new_descriptions = request.form.getlist("new_collection_descriptions[]")
        new_show_on_home = request.form.getlist("new_collection_show_on_home[]")
        new_home_indexes = request.form.getlist("new_collection_home_indexes[]")
        new_image_files = request.files.getlist("new_collection_images[]")

        for i, col_name in enumerate(new_names):
            if not col_name.strip():
                continue

            col_image_url = None
            if i < len(new_image_files) and new_image_files[i].filename:
                col_uploaded, col_error = upload_images(
                    new_image_files[i], folder="package-collections"
                )
                if col_error:
                    db.session.rollback()
                    return (
                        jsonify(
                            {
                                "status": "error",
                                "message": f"Collection image error: {col_error}",
                            }
                        ),
                        400,
                    )
                col_image_url = col_uploaded[0]["url"]

            show_home = (
                new_show_on_home[i].lower() == "true"
                if i < len(new_show_on_home)
                else False
            )
            try:
                home_idx = int(new_home_indexes[i]) if i < len(new_home_indexes) else 0
            except (ValueError, TypeError):
                home_idx = 0

            col = PackageCollection(
                country_id=country.id,
                name=col_name.strip(),
                description=(
                    new_descriptions[i].strip() if i < len(new_descriptions) else ""
                ),
                image=col_image_url or "",
                show_on_home=show_home,
                home_index=home_idx,
            )
            db.session.add(col)

        update_ids = request.form.getlist("update_collection_ids[]")
        update_names = request.form.getlist("update_collection_names[]")
        update_descriptions = request.form.getlist("update_collection_descriptions[]")
        update_image_files = request.files.getlist("update_collection_images[]")

        for i, col_id_str in enumerate(update_ids):
            try:
                col_id = int(col_id_str)
            except (ValueError, TypeError):
                continue

            col = PackageCollection.query.get(col_id)
            if not col or col.country_id != country.id:
                continue

            if i < len(update_names) and update_names[i].strip():
                col.name = update_names[i].strip()
            if i < len(update_descriptions):
                col.description = update_descriptions[i].strip()
            if i < len(update_image_files) and update_image_files[i].filename:
                if col.image:
                    old_pid = "/".join(col.image.split("/")[-2:]).rsplit(".", 1)[0]
                    delete_images({"public_id": old_pid})
                col_uploaded, col_error = upload_images(
                    update_image_files[i], folder="package-collections"
                )
                if col_error:
                    db.session.rollback()
                    return (
                        jsonify(
                            {
                                "status": "error",
                                "message": f"Collection image error: {col_error}",
                            }
                        ),
                        400,
                    )
                col.image = col_uploaded[0]["url"]

        remove_ids = request.form.getlist("remove_collection_ids[]")
        for col_id_str in remove_ids:
            try:
                col_id = int(col_id_str)
            except (ValueError, TypeError):
                continue
            col = PackageCollection.query.get(col_id)
            if col and col.country_id == country.id:
                if col.image:
                    old_pid = "/".join(col.image.split("/")[-2:]).rsplit(".", 1)[0]
                    delete_images({"public_id": old_pid})
                db.session.delete(col)

        db.session.commit()

        updated_collections = PackageCollection.query.filter_by(
            country_id=country.id
        ).all()

        return (
            jsonify(
                {
                    "status": "success",
                    "message": "Country updated successfully",
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
                                "show_on_home": c.show_on_home,
                                "home_index": c.home_index,
                                "total_packages": len(c.packages),
                            }
                            for c in updated_collections
                        ],
                    },
                }
            ),
            200,
        )

    except Exception as e:
        db.session.rollback()
        return jsonify({"status": "error", "message": str(e)}), 500


@adminBP.route("/country/<int:country_id>", methods=["DELETE"])
@middleware
def delete_country(country_id):
    try:
        country = Country.query.get(country_id)
        if not country:
            return jsonify({"status": "error", "message": "Country not found"}), 404

        for col in country.package_collections:
            if col.image:
                col_pid = "/".join(col.image.split("/")[-2:]).rsplit(".", 1)[0]
                delete_images({"public_id": col_pid})

        if country.image:
            public_id = "/".join(country.image.split("/")[-2:]).rsplit(".", 1)[0]
            delete_images({"public_id": public_id})

        db.session.delete(country)
        db.session.commit()

        return (
            jsonify({"status": "success", "message": "Country deleted successfully"}),
            200,
        )

    except Exception as e:
        db.session.rollback()
        return jsonify({"status": "error", "message": str(e)}), 500


# CREATE package collection
@adminBP.route("/package-collection", methods=["POST"])
@middleware
def create_package_collection():
    try:
        country_id = request.form.get("country_id")
        name = request.form.get("name")
        description = request.form.get("description")
        image_file = request.files.get("image")
        show_on_home = request.form.get("show_on_home", "false").lower() == "true"
        home_index = request.form.get("home_index", 0)

        if not name:
            return jsonify({"status": "error", "message": "Name is required"}), 400
        if not image_file:
            return jsonify({"status": "error", "message": "Image is required"}), 400

        if country_id:
            country = Country.query.get(country_id)
            if not country:
                return jsonify({"status": "error", "message": "Country not found"}), 404

        try:
            home_index = int(home_index)
        except (ValueError, TypeError):
            return (
                jsonify(
                    {"status": "error", "message": "home_index must be an integer"}
                ),
                400,
            )

        uploaded, error = upload_images(image_file, folder="package-collections")
        if error:
            return jsonify({"status": "error", "message": error}), 400

        collection = PackageCollection(
            country_id=int(country_id) if country_id else None,
            name=name,
            description=description,
            image=uploaded[0]["url"],
            show_on_home=show_on_home,
            home_index=home_index,
        )
        db.session.add(collection)
        db.session.commit()

        return (
            jsonify(
                {
                    "status": "success",
                    "message": "Package collection created successfully",
                    "data": {
                        "id": collection.id,
                        "name": collection.name,
                        "description": collection.description,
                        "image": collection.image,
                        "country_id": collection.country_id,
                        "show_on_home": collection.show_on_home,
                        "home_index": collection.home_index,
                    },
                }
            ),
            201,
        )

    except Exception as e:
        db.session.rollback()
        return jsonify({"status": "error", "message": str(e)}), 500


@adminBP.route("/package-collection", methods=["GET"])
@middleware
def get_package_collections():
    try:
        page = request.args.get("page", 1, type=int)
        per_page = min(request.args.get("per_page", 10, type=int), 100)
        search = request.args.get("search", "").strip()
        country_id = request.args.get("country_id", type=int)  # filter by country
        show_on_home = request.args.get("show_on_home")  # "true" | "false"
        sort_by = request.args.get("sort_by", "id")  # id | name | home_index
        order = request.args.get("order", "desc")  # asc | desc
        no_country = request.args.get("no_country")  # "true" → unlinked only

        query = PackageCollection.query

        if search:
            query = query.filter(
                db.or_(
                    PackageCollection.name.ilike(f"%{search}%"),
                    PackageCollection.description.ilike(f"%{search}%"),
                )
            )

        if country_id is not None:
            query = query.filter(PackageCollection.country_id == country_id)

        if no_country and no_country.lower() == "true":
            query = query.filter(PackageCollection.country_id.is_(None))

        if show_on_home is not None:
            query = query.filter(
                PackageCollection.show_on_home == (show_on_home.lower() == "true")
            )

        sort_column_map = {
            "id": PackageCollection.id,
            "name": PackageCollection.name,
            "home_index": PackageCollection.home_index,
        }
        sort_col = sort_column_map.get(sort_by, PackageCollection.id)
        query = query.order_by(sort_col.asc() if order == "asc" else sort_col.desc())

        total = query.count()
        collections = query.offset((page - 1) * per_page).limit(per_page).all()

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
                            "show_on_home": c.show_on_home,
                            "home_index": c.home_index,
                            "total_packages": len(c.packages),
                            "packages": [
                                {
                                    "id": p.id,
                                    "name": p.name,
                                    "total_price": p.total_price,
                                    "discount_price": p.discount_price,
                                    "person": p.person,
                                    "image": p.image,
                                }
                                for p in c.packages
                            ],
                        }
                        for c in collections
                    ],
                    "pagination": {
                        "page": page,
                        "per_page": per_page,
                        "total": total,
                        "pages": (total + per_page - 1) // per_page,
                        "has_prev": page > 1,
                        "has_next": page * per_page < total,
                    },
                }
            ),
            200,
        )

    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500


@adminBP.route("/package-collection/<int:collection_id>", methods=["GET"])
@middleware
def get_package_collection(collection_id):
    try:
        collection = PackageCollection.query.get(collection_id)
        if not collection:
            return (
                jsonify({"status": "error", "message": "Package collection not found"}),
                404,
            )

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
                        "show_on_home": collection.show_on_home,
                        "home_index": collection.home_index,
                        "packages": [
                            {
                                "id": p.id,
                                "name": p.name,
                                "description": p.description,
                                "total_price": p.total_price,
                                "discount_price": p.discount_price,
                                "person": p.person,
                                "image": p.image,
                                "reviews": [
                                    {
                                        "id": r.id,
                                        "name": r.name,
                                        "star": r.star,
                                        "review": r.review,
                                    }
                                    for r in p.reviews
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


@adminBP.route("/package-collection/bulk-delete", methods=["DELETE"])
@middleware
def delete_package_collections():
    try:
        data = request.get_json()
        collection_ids = data.get("collection_ids", [])

        if not collection_ids or not isinstance(collection_ids, list):
            return (
                jsonify(
                    {
                        "status": "error",
                        "message": "collection_ids must be a non-empty list",
                    }
                ),
                400,
            )

        deleted, not_found = [], []

        for cid in collection_ids:
            collection = PackageCollection.query.get(cid)
            if not collection:
                not_found.append(cid)
                continue

            if collection.image:
                public_id = "/".join(collection.image.split("/")[-2:]).rsplit(".", 1)[0]
                delete_images({"public_id": public_id})

            for package in collection.packages:
                if package.image:
                    delete_images(package.image, folder="packages")

            db.session.delete(collection)
            deleted.append(cid)

        db.session.commit()

        return (
            jsonify(
                {
                    "status": "success",
                    "message": f"{len(deleted)} collection(s) deleted successfully",
                    "deleted": deleted,
                    "not_found": not_found,
                }
            ),
            200,
        )

    except Exception as e:
        db.session.rollback()
        return jsonify({"status": "error", "message": str(e)}), 500


# DELETE single package collection
@adminBP.route("/package-collection/<int:collection_id>", methods=["DELETE"])
@middleware
def delete_package_collection(collection_id):
    try:
        collection = PackageCollection.query.get(collection_id)
        if not collection:
            return (
                jsonify({"status": "error", "message": "Package collection not found"}),
                404,
            )

        if collection.image:
            public_id = "/".join(collection.image.split("/")[-2:]).rsplit(".", 1)[0]
            delete_images({"public_id": public_id})

        for package in collection.packages:
            if package.image:
                delete_images(package.image, folder="packages")

        db.session.delete(collection)
        db.session.commit()

        return (
            jsonify(
                {
                    "status": "success",
                    "message": "Package collection deleted successfully",
                }
            ),
            200,
        )

    except Exception as e:
        db.session.rollback()
        return jsonify({"status": "error", "message": str(e)}), 500


@adminBP.route("/package-collection/<int:collection_id>", methods=["PUT"])
@middleware
def edit_package_collection(collection_id):
    try:
        collection = PackageCollection.query.get(collection_id)
        if not collection:
            return (
                jsonify({"status": "error", "message": "Package collection not found"}),
                404,
            )

        name = request.form.get("name")
        description = request.form.get("description")
        image_file = request.files.get("image")
        show_on_home = request.form.get("show_on_home")
        home_index = request.form.get("home_index")
        country_id_raw = request.form.get("country_id")  # '' = unlink, None = not sent

        if name:
            collection.name = name

        if description is not None:
            collection.description = description

        if show_on_home is not None:
            collection.show_on_home = show_on_home.lower() == "true"

        if home_index is not None:
            try:
                collection.home_index = int(home_index)
            except (ValueError, TypeError):
                return (
                    jsonify(
                        {"status": "error", "message": "home_index must be an integer"}
                    ),
                    400,
                )

        if country_id_raw is not None:
            if country_id_raw == "" or country_id_raw.lower() == "null":
                collection.country_id = None
            else:
                try:
                    new_country_id = int(country_id_raw)
                    country = Country.query.get(new_country_id)
                    if not country:
                        return (
                            jsonify(
                                {"status": "error", "message": "Country not found"}
                            ),
                            404,
                        )
                    collection.country_id = new_country_id
                except (ValueError, TypeError):
                    return (
                        jsonify({"status": "error", "message": "Invalid country_id"}),
                        400,
                    )

        if image_file:
            if collection.image:
                public_id = "/".join(collection.image.split("/")[-2:]).rsplit(".", 1)[0]
                delete_images({"public_id": public_id})
            uploaded, error = upload_images(image_file, folder="package-collections")
            if error:
                return jsonify({"status": "error", "message": error}), 400
            collection.image = uploaded[0]["url"]

        added, skipped_add, not_found_add = [], [], []
        removed, skipped_remove, not_found_remove = [], [], []

        body = request.get_json(silent=True) or {}
        add_ids = body.get("add_package_ids", [])
        remove_ids = body.get("remove_package_ids", [])

        for pid in add_ids:
            package = Package.query.get(pid)
            if not package:
                not_found_add.append(pid)
            elif package.package_collection_id == collection_id:
                skipped_add.append(pid)
            else:
                package.package_collection_id = collection_id
                added.append(pid)

        for pid in remove_ids:
            package = Package.query.get(pid)
            if not package:
                not_found_remove.append(pid)
            elif package.package_collection_id != collection_id:
                skipped_remove.append(pid)
            else:
                package.package_collection_id = None
                removed.append(pid)

        db.session.commit()

        response = {
            "status": "success",
            "message": "Package collection updated successfully",
            "data": {
                "id": collection.id,
                "name": collection.name,
                "description": collection.description,
                "image": collection.image,
                "country_id": collection.country_id,
                "show_on_home": collection.show_on_home,
                "home_index": collection.home_index,
            },
        }

        if add_ids:
            response["packages_added"] = {
                "added": added,
                "skipped": skipped_add,
                "not_found": not_found_add,
            }
        if remove_ids:
            response["packages_removed"] = {
                "removed": removed,
                "skipped": skipped_remove,
                "not_found": not_found_remove,
            }

        return jsonify(response), 200

    except Exception as e:
        db.session.rollback()
        return jsonify({"status": "error", "message": str(e)}), 500


# CREATE package
@adminBP.route("/package", methods=["POST"])
@middleware
def create_package():
    try:
        package_collection_id = request.form.get("package_collection_id")
        name = request.form.get("name")
        description = request.form.get("description")
        total_price = request.form.get("total_price")
        discount_price = request.form.get("discount_price")
        person = request.form.get("person", 1)
        image_files = request.files.getlist("images")
        days_data = request.form.get("days")

        if not package_collection_id:
            return (
                jsonify(
                    {"status": "error", "message": "Package collection ID is required"}
                ),
                400,
            )
        if not name:
            return jsonify({"status": "error", "message": "Name is required"}), 400
        if not total_price:
            return (
                jsonify({"status": "error", "message": "Total price is required"}),
                400,
            )
        if not discount_price:
            return (
                jsonify({"status": "error", "message": "Discount price is required"}),
                400,
            )

        collection = PackageCollection.query.get(package_collection_id)
        if not collection:
            return (
                jsonify({"status": "error", "message": "Package collection not found"}),
                404,
            )

        uploaded_images = None
        if image_files:
            uploaded_images, error = upload_images(image_files, folder="packages")
            if error:
                return jsonify({"status": "error", "message": error}), 400

        days_list = json.loads(days_data) if days_data else []

        package = Package(
            package_collection_id=int(package_collection_id),
            name=name,
            description=description,
            total_price=float(total_price),
            discount_price=float(discount_price),
            person=int(person),
            image=uploaded_images,
        )
        db.session.add(package)
        db.session.flush()  # get package.id before committing

        for day_data in days_list:
            package_day = PackageDays(
                package_id=package.id,
                days=int(day_data.get("days")),
                price=float(day_data.get("price", 0)),
                discount_price=float(day_data.get("discount_price", 0)),
            )
            db.session.add(package_day)
            db.session.flush()

            for activity in day_data.get("activities", []):
                db.session.add(
                    Activities(
                        package_days_id=package_day.id,
                        day=activity.get("day"),
                        description=activity.get("description"),
                    )
                )

            for desc in day_data.get("day_description", []):
                db.session.add(
                    DaysDescription(
                        package_days_id=package_day.id,
                        day=desc.get("day"),
                        description=desc.get("description"),
                    )
                )

        db.session.commit()

        return (
            jsonify(
                {
                    "status": "success",
                    "message": "Package created successfully",
                    "data": {
                        "id": package.id,
                        "name": package.name,
                        "description": package.description,
                        "total_price": package.total_price,
                        "discount_price": package.discount_price,
                        "person": package.person,
                        "image": package.image,
                    },
                }
            ),
            201,
        )

    except Exception as e:
        db.session.rollback()
        return jsonify({"status": "error", "message": str(e)}), 500


# GET all packages  - need pagination and filter
@adminBP.route("/package", methods=["GET"])
@middleware
def get_packages():
    try:
        page = request.args.get("page", 1, type=int)
        per_page = min(request.args.get("per_page", 10, type=int), 100)
        search = request.args.get("search", "").strip()
        collection_id = request.args.get("collection_id", type=int)
        min_price = request.args.get("min_price", type=float)
        max_price = request.args.get("max_price", type=float)
        sort_by = request.args.get("sort_by", "id")
        order = request.args.get("order", "desc")

        query = Package.query

        if search:
            query = query.filter(
                db.or_(
                    Package.name.ilike(f"%{search}%"),
                    Package.description.ilike(f"%{search}%"),
                )
            )

        if collection_id is not None:
            query = query.filter(Package.package_collection_id == collection_id)

        if min_price is not None:
            query = query.filter(Package.discount_price >= min_price)

        if max_price is not None:
            query = query.filter(Package.discount_price <= max_price)

        sort_map = {
            "id": Package.id,
            "name": Package.name,
            "price": Package.discount_price,
            "total_price": Package.total_price,
        }
        sort_col = sort_map.get(sort_by, Package.id)
        query = query.order_by(sort_col.asc() if order == "asc" else sort_col.desc())

        total = query.count()
        packages = query.offset((page - 1) * per_page).limit(per_page).all()

        return (
            jsonify(
                {
                    "status": "success",
                    "data": [
                        {
                            "id": p.id,
                            "name": p.name,
                            "description": p.description,
                            "total_price": p.total_price,
                            "discount_price": p.discount_price,
                            "person": p.person,
                            "image": p.image,
                            "package_collection_id": p.package_collection_id,
                            "reviews": [
                                {
                                    "id": r.id,
                                    "name": r.name,
                                    "star": r.star,
                                    "review": r.review,
                                }
                                for r in p.reviews
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
                                for d in p.days
                            ],
                        }
                        for p in packages
                    ],
                    "pagination": {
                        "page": page,
                        "per_page": per_page,
                        "total": total,
                        "pages": (total + per_page - 1) // per_page,
                        "has_prev": page > 1,
                        "has_next": page * per_page < total,
                    },
                }
            ),
            200,
        )

    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500


@adminBP.route("/package/<int:package_id>", methods=["GET"])
@middleware
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
                        "package_collection_id": package.package_collection_id,
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


@adminBP.route("/package/<int:package_id>", methods=["PUT"])
@middleware
def update_package(package_id):
    try:
        package = Package.query.get(package_id)
        if not package:
            return jsonify({"status": "error", "message": "Package not found"}), 404

        package_collection_id = request.form.get("package_collection_id")
        name = request.form.get("name")
        description = request.form.get("description")
        total_price = request.form.get("total_price")
        discount_price = request.form.get("discount_price")
        person = request.form.get("person")
        image_files = request.files.getlist("images")
        days_data = request.form.get("days")

        if package_collection_id:
            collection = PackageCollection.query.get(package_collection_id)
            if not collection:
                return (
                    jsonify(
                        {"status": "error", "message": "Package collection not found"}
                    ),
                    404,
                )
            package.package_collection_id = int(package_collection_id)

        if name:
            package.name = name
        if description is not None:
            package.description = description
        if total_price:
            package.total_price = float(total_price)
        if discount_price:
            package.discount_price = float(discount_price)
        if person:
            package.person = int(person)

        if image_files and any(f.filename for f in image_files):
            if package.image:
                delete_images(package.image)

            uploaded_images, error = upload_images(image_files, folder="packages")
            if error:
                return jsonify({"status": "error", "message": error}), 400

            package.image = uploaded_images

        if days_data:
            days_list = json.loads(days_data)

            package.days.clear()
            db.session.flush()

            for day_data in days_list:
                package_day = PackageDays(
                    package_id=package.id,
                    days=int(day_data.get("days")),
                    price=float(day_data.get("price", 0)),
                    discount_price=float(day_data.get("discount_price", 0)),
                )
                db.session.add(package_day)
                db.session.flush()

                for activity in day_data.get("activities", []):
                    db.session.add(
                        Activities(
                            package_days_id=package_day.id,
                            day=activity.get("day"),
                            description=activity.get("description"),
                        )
                    )

                for desc in day_data.get("day_description", []):
                    db.session.add(
                        DaysDescription(
                            package_days_id=package_day.id,
                            day=desc.get("day"),
                            description=desc.get("description"),
                        )
                    )

        db.session.commit()

        return (
            jsonify(
                {
                    "status": "success",
                    "message": "Package updated successfully",
                    "data": {
                        "id": package.id,
                        "name": package.name,
                        "description": package.description,
                        "total_price": package.total_price,
                        "discount_price": package.discount_price,
                        "person": package.person,
                        "image": package.image,
                    },
                }
            ),
            200,
        )

    except Exception as e:
        db.session.rollback()
        return jsonify({"status": "error", "message": str(e)}), 500


@adminBP.route("/package/<int:package_id>", methods=["DELETE"])
@middleware
def delete_package(package_id):
    try:
        package = Package.query.get(package_id)
        if not package:
            return jsonify({"status": "error", "message": "Package not found"}), 404

        if package.image:
            delete_images(package.image)

        db.session.delete(package)
        db.session.commit()

        return (
            jsonify(
                {
                    "status": "success",
                    "message": "Package deleted successfully",
                }
            ),
            200,
        )

    except Exception as e:
        db.session.rollback()
        return jsonify({"status": "error", "message": str(e)}), 500


# GET all enquiries
@adminBP.route("/enquiries", methods=["GET"])
@middleware
def get_enquiries():
    try:
        page = request.args.get("page", 1, type=int)
        per_page = request.args.get("per_page", 10, type=int)

        paginated = Form.query.order_by(Form.id.desc()).paginate(
            page=page, per_page=per_page, error_out=False
        )

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
                            "id": f.id,
                            "full_name": f.full_name,
                            "email": f.email,
                            "phoneNumber": f.phoneNumber,
                            "message": f.message,
                            "package_id": f.package_id,
                            "package_details": (
                                json.loads(f.package_details)
                                if f.package_details
                                else None
                            ),
                        }
                        for f in paginated.items
                    ],
                }
            ),
            200,
        )

    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500


# GET single enquiry
@adminBP.route("/enquiries/<int:form_id>", methods=["GET"])
@middleware
def get_enquiry(form_id):
    try:
        form = Form.query.get(form_id)
        if not form:
            return jsonify({"status": "error", "message": "Enquiry not found"}), 404

        return (
            jsonify(
                {
                    "status": "success",
                    "data": {
                        "id": form.id,
                        "full_name": form.full_name,
                        "email": form.email,
                        "phoneNumber": form.phoneNumber,
                        "message": form.message,
                        "package_id": form.package_id,
                        "package_details": (
                            json.loads(form.package_details)
                            if form.package_details
                            else None
                        ),
                    },
                }
            ),
            200,
        )

    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500


# DELETE enquiry
@adminBP.route("/enquiries/<int:form_id>", methods=["DELETE"])
@middleware
def delete_enquiry(form_id):
    try:
        form = Form.query.get(form_id)
        if not form:
            return jsonify({"status": "error", "message": "Enquiry not found"}), 404

        db.session.delete(form)
        db.session.commit()

        return (
            jsonify(
                {
                    "status": "success",
                    "message": "Enquiry deleted successfully",
                }
            ),
            200,
        )

    except Exception as e:
        db.session.rollback()
        return jsonify({"status": "error", "message": str(e)}), 500


# GET all reviews (across all packages)
@adminBP.route("/reviews", methods=["GET"])
@middleware
def get_reviews():
    try:
        page = request.args.get("page", 1, type=int)
        per_page = request.args.get("per_page", 10, type=int)

        paginated = Review.query.order_by(Review.id.desc()).paginate(
            page=page, per_page=per_page, error_out=False
        )

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
                            "id": r.id,
                            "name": r.name,
                            "star": r.star,
                            "review": r.review,
                            "package_id": r.package_id,
                            "package_name": r.package.name if r.package else None,
                        }
                        for r in paginated.items
                    ],
                }
            ),
            200,
        )

    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500


# DELETE review
@adminBP.route("/reviews/<int:review_id>", methods=["DELETE"])
@middleware
def delete_review(review_id):
    try:
        review = Review.query.get(review_id)
        if not review:
            return jsonify({"status": "error", "message": "Review not found"}), 404

        db.session.delete(review)
        db.session.commit()

        return (
            jsonify(
                {
                    "status": "success",
                    "message": "Review deleted successfully",
                }
            ),
            200,
        )

    except Exception as e:
        db.session.rollback()
        return jsonify({"status": "error", "message": str(e)}), 500


@adminBP.route("/dashboard", methods=["GET"])
@middleware
def get_dashboard():
    try:

        # ---- Overview counts ----
        total_countries = Country.query.count()
        total_collections = PackageCollection.query.count()
        total_packages = Package.query.count()
        total_enquiries = Form.query.count()
        total_reviews = Review.query.count()

        # ---- Top 5 packages by enquiries ----
        top_packages_by_enquiries = (
            db.session.query(
                Package.id,
                Package.name,
                Package.total_price,
                Package.discount_price,
                Package.image,
                db.func.count(Form.id).label("total_enquiries"),
            )
            .outerjoin(Form, Form.package_id == Package.id)
            .group_by(Package.id)
            .order_by(db.func.count(Form.id).desc())
            .limit(5)
            .all()
        )

        # ---- Top 5 packages by average rating ----
        top_packages_by_rating = (
            db.session.query(
                Package.id,
                Package.name,
                Package.total_price,
                Package.discount_price,
                Package.image,
                db.func.round(db.func.avg(Review.star), 1).label("average_rating"),
                db.func.count(Review.id).label("total_reviews"),
            )
            .outerjoin(Review, Review.package_id == Package.id)
            .group_by(Package.id)
            .order_by(db.func.avg(Review.star).desc())
            .having(db.func.count(Review.id) > 0)
            .limit(5)
            .all()
        )

        # ---- Top 5 packages by reviews count ----
        top_packages_by_reviews = (
            db.session.query(
                Package.id,
                Package.name,
                Package.image,
                db.func.count(Review.id).label("total_reviews"),
                db.func.round(db.func.avg(Review.star), 1).label("average_rating"),
            )
            .outerjoin(Review, Review.package_id == Package.id)
            .group_by(Package.id)
            .order_by(db.func.count(Review.id).desc())
            .having(db.func.count(Review.id) > 0)
            .limit(5)
            .all()
        )

        # ---- Top 5 countries by package count ----
        top_countries = (
            db.session.query(
                Country.id,
                Country.name,
                Country.image,
                db.func.count(Package.id).label("total_packages"),
            )
            .outerjoin(PackageCollection, PackageCollection.country_id == Country.id)
            .outerjoin(Package, Package.package_collection_id == PackageCollection.id)
            .group_by(Country.id)
            .order_by(db.func.count(Package.id).desc())
            .limit(5)
            .all()
        )

        # ---- Top 5 collections by package count ----
        top_collections = (
            db.session.query(
                PackageCollection.id,
                PackageCollection.name,
                PackageCollection.image,
                PackageCollection.country_id,
                db.func.count(Package.id).label("total_packages"),
            )
            .outerjoin(Package, Package.package_collection_id == PackageCollection.id)
            .group_by(PackageCollection.id)
            .order_by(db.func.count(Package.id).desc())
            .limit(5)
            .all()
        )

        # ---- Recent 5 enquiries ----
        recent_enquiries = Form.query.order_by(Form.id.desc()).limit(5).all()

        # ---- Recent 5 reviews ----
        recent_reviews = Review.query.order_by(Review.id.desc()).limit(5).all()

        # ---- Star rating distribution (across all packages) ----
        star_distribution = (
            db.session.query(Review.star, db.func.count(Review.id).label("count"))
            .group_by(Review.star)
            .order_by(Review.star.desc())
            .all()
        )

        # ---- Packages with no enquiries (underperforming) ----
        no_enquiry_packages = (
            db.session.query(Package)
            .outerjoin(Form, Form.package_id == Package.id)
            .group_by(Package.id)
            .having(db.func.count(Form.id) == 0)
            .limit(5)
            .all()
        )

        return (
            jsonify(
                {
                    "status": "success",
                    "data": {
                        # --- Overview ---
                        "overview": {
                            "total_countries": total_countries,
                            "total_collections": total_collections,
                            "total_packages": total_packages,
                            "total_enquiries": total_enquiries,
                            "total_reviews": total_reviews,
                        },
                        # --- Top performing packages ---
                        "top_packages_by_enquiries": [
                            {
                                "id": p.id,
                                "name": p.name,
                                "total_price": p.total_price,
                                "discount_price": p.discount_price,
                                "image": p.image,
                                "total_enquiries": p.total_enquiries,
                            }
                            for p in top_packages_by_enquiries
                        ],
                        "top_packages_by_rating": [
                            {
                                "id": p.id,
                                "name": p.name,
                                "total_price": p.total_price,
                                "discount_price": p.discount_price,
                                "image": p.image,
                                "average_rating": (
                                    float(p.average_rating) if p.average_rating else 0
                                ),
                                "total_reviews": p.total_reviews,
                            }
                            for p in top_packages_by_rating
                        ],
                        "top_packages_by_reviews": [
                            {
                                "id": p.id,
                                "name": p.name,
                                "image": p.image,
                                "total_reviews": p.total_reviews,
                                "average_rating": (
                                    float(p.average_rating) if p.average_rating else 0
                                ),
                            }
                            for p in top_packages_by_reviews
                        ],
                        # --- Top countries and collections ---
                        "top_countries": [
                            {
                                "id": c.id,
                                "name": c.name,
                                "image": c.image,
                                "total_packages": c.total_packages,
                            }
                            for c in top_countries
                        ],
                        "top_collections": [
                            {
                                "id": c.id,
                                "name": c.name,
                                "image": c.image,
                                "country_id": c.country_id,
                                "total_packages": c.total_packages,
                            }
                            for c in top_collections
                        ],
                        # --- Recent activity ---
                        "recent_enquiries": [
                            {
                                "id": f.id,
                                "full_name": f.full_name,
                                "email": f.email,
                                "phoneNumber": f.phoneNumber,
                                "message": f.message,
                                "package_id": f.package_id,
                                "package_details": (
                                    json.loads(f.package_details)
                                    if f.package_details
                                    else None
                                ),
                            }
                            for f in recent_enquiries
                        ],
                        "recent_reviews": [
                            {
                                "id": r.id,
                                "name": r.name,
                                "star": r.star,
                                "review": r.review,
                                "package_id": r.package_id,
                                "package_name": r.package.name if r.package else None,
                            }
                            for r in recent_reviews
                        ],
                        # --- Insights ---
                        "star_distribution": [
                            {
                                "star": s.star,
                                "count": s.count,
                            }
                            for s in star_distribution
                        ],
                        "underperforming_packages": [
                            {
                                "id": p.id,
                                "name": p.name,
                                "total_price": p.total_price,
                                "discount_price": p.discount_price,
                                "image": p.image,
                            }
                            for p in no_enquiry_packages
                        ],
                    },
                }
            ),
            200,
        )

    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500


# ==================== ADMIN BANNER ROUTES ====================

MAX_BANNERS = 4


# CREATE banner
@adminBP.route("/banner", methods=["POST"])
@middleware
def create_banner():
    try:
        image_file = request.files.get("image")
        link = request.form.get("link")

        if not image_file:
            return jsonify({"status": "error", "message": "Image is required"}), 400
        if not link:
            return jsonify({"status": "error", "message": "Link is required"}), 400

        # --- Max 4 banners check ---
        current_count = Banner.query.count()
        if current_count >= MAX_BANNERS:
            return (
                jsonify(
                    {
                        "status": "error",
                        "message": f"Maximum {MAX_BANNERS} banners allowed. Please delete one before adding a new one.",
                    }
                ),
                400,
            )

        uploaded, error = upload_images(image_file, folder="banners")
        if error:
            return jsonify({"status": "error", "message": error}), 400

        banner = Banner(
            image=uploaded[0]["url"],
            link=link,
        )
        db.session.add(banner)
        db.session.commit()

        return (
            jsonify(
                {
                    "status": "success",
                    "message": "Banner created successfully",
                    "data": {
                        "id": banner.id,
                        "image": banner.image,
                        "link": banner.link,
                    },
                }
            ),
            201,
        )

    except Exception as e:
        db.session.rollback()
        return jsonify({"status": "error", "message": str(e)}), 500


# GET all banners
@adminBP.route("/banner", methods=["GET"])
@middleware
def get_banners():
    try:
        banners = Banner.query.all()

        return (
            jsonify(
                {
                    "status": "success",
                    "data": [
                        {
                            "id": b.id,
                            "image": b.image,
                            "link": b.link,
                        }
                        for b in banners
                    ],
                    "total": len(banners),
                    "remaining_slots": MAX_BANNERS - len(banners),
                }
            ),
            200,
        )

    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500


# UPDATE banner
@adminBP.route("/banner/<int:banner_id>", methods=["PUT"])
@middleware
def update_banner(banner_id):
    try:
        banner = Banner.query.get(banner_id)
        if not banner:
            return jsonify({"status": "error", "message": "Banner not found"}), 404

        image_file = request.files.get("image")
        link = request.form.get("link")

        if link:
            banner.link = link

        if image_file:
            if banner.image:
                public_id = "/".join(banner.image.split("/")[-2:]).rsplit(".", 1)[0]
                delete_images({"public_id": public_id})

            uploaded, error = upload_images(image_file, folder="banners")
            if error:
                return jsonify({"status": "error", "message": error}), 400

            banner.image = uploaded[0]["url"]

        db.session.commit()

        return (
            jsonify(
                {
                    "status": "success",
                    "message": "Banner updated successfully",
                    "data": {
                        "id": banner.id,
                        "image": banner.image,
                        "link": banner.link,
                    },
                }
            ),
            200,
        )

    except Exception as e:
        db.session.rollback()
        return jsonify({"status": "error", "message": str(e)}), 500


# DELETE banner
@adminBP.route("/banner/<int:banner_id>", methods=["DELETE"])
@middleware
def delete_banner(banner_id):
    try:
        banner = Banner.query.get(banner_id)
        if not banner:
            return jsonify({"status": "error", "message": "Banner not found"}), 404

        if banner.image:
            public_id = "/".join(banner.image.split("/")[-2:]).rsplit(".", 1)[0]
            delete_images({"public_id": public_id})

        db.session.delete(banner)
        db.session.commit()

        return (
            jsonify(
                {
                    "status": "success",
                    "message": "Banner deleted successfully",
                }
            ),
            200,
        )

    except Exception as e:
        db.session.rollback()
        return jsonify({"status": "error", "message": str(e)}), 500


# ==================== USER BANNER ROUTE ====================
