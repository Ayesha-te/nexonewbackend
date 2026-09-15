import cloudinary
import cloudinary.uploader
import cloudinary.utils
from django.core.files.storage import Storage
from django.utils.deconstruct import deconstructible


@deconstructible
class VideoCloudinaryStorage(Storage):
    """Uploads ad video files to Cloudinary as resource_type="video".

    django-cloudinary-storage's own MediaCloudinaryStorage uploads through Cloudinary's
    image endpoint, which rejects video files with "Invalid image file". This talks to the
    cloudinary SDK's public, documented upload/destroy functions directly instead of relying
    on that package's internals, so it works regardless of the installed package version.
    """

    def _open(self, name, mode="rb"):
        raise NotImplementedError("Reading ad video files back through Django is not supported; use .url() instead.")

    def _save(self, name, content):
        result = cloudinary.uploader.upload(
            content,
            resource_type="video",
            folder="ads-videos",
            use_filename=True,
            unique_filename=True,
            overwrite=False,
        )
        public_id = result.get("public_id", name)
        file_format = result.get("format")
        return f"{public_id}.{file_format}" if file_format else public_id

    def _public_id(self, name):
        return name.rsplit(".", 1)[0] if "." in name else name

    def exists(self, name):
        # Cloudinary guarantees a unique public_id per upload (unique_filename=True), so
        # there's never a pre-existing name to collide with from Django's point of view.
        return False

    def url(self, name):
        if not name:
            return None
        public_id = self._public_id(name)
        file_format = name.rsplit(".", 1)[1] if "." in name else None
        url, _options = cloudinary.utils.cloudinary_url(public_id, resource_type="video", format=file_format)
        return url

    def delete(self, name):
        cloudinary.uploader.destroy(self._public_id(name), resource_type="video")

    def size(self, name):
        return 0

    def get_available_name(self, name, max_length=None):
        return name
