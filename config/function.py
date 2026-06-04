import cloudinary.uploader

ALLOWED_EXTENSIONS = {"jpg", "jpeg", "png", "webp"}


def upload_images(files, folder="uploads", quality=75):
    try:
        if not files:
            return None, "No images provided"

        if not isinstance(files, list):
            files = [files]

        uploaded, failed = [], []

        for file in files:
            if not file or not getattr(file, "filename", None):
                continue

            ext = file.filename.rsplit(".", 1)[-1].lower()
            if ext not in ALLOWED_EXTENSIONS:
                failed.append(file.filename)
                continue

            file.seek(0)
            result = cloudinary.uploader.upload(
                file,
                folder=folder,
                resource_type="image",
                quality=quality,
                fetch_format="auto",
                flags="progressive",
            )

            uploaded.append(
                {
                    "url": result.get("secure_url"),
                    "public_id": result.get("public_id"),
                }
            )

        if not uploaded:
            msg = "No valid images uploaded"
            if failed:
                msg += f". Invalid files: {', '.join(failed)}"
            return None, msg

        return uploaded, None

    except Exception as e:
        return None, str(e)


def delete_images(images, folder="uploads"):
    try:
        if not images:
            return False, "No images provided"

        if isinstance(images, str):
            images = [{"public_id": images}]
        elif isinstance(images, dict):
            images = [images]

        failed = []

        for image in images:
            public_id = image.get("public_id") if isinstance(image, dict) else image
            if not public_id:
                continue

            result = cloudinary.uploader.destroy(public_id, resource_type="image")
            if result.get("result") != "ok":
                failed.append(public_id)

        if failed:
            return False, f"Failed to delete: {', '.join(failed)}"

        return True, None
    except Exception as e:
        return False, str(e)
