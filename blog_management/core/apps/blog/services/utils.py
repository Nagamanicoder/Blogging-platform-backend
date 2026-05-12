import cloudinary.uploader

FOLDER = 'blog-images/'

def upload_image(image_file):
    result = cloudinary.uploader.upload(image_file, folder=FOLDER)
    return {
        'image_url': result['secure_url'],
        'object_key': result['public_id'],  
    }

def replace_image(image_file, object_key):
    # Uploads new image using the same object_key — Cloudinary overwrites it
    result = cloudinary.uploader.upload(
        image_file,
        public_id=object_key,
        overwrite=True,
        invalidate=True,    # clears CDN cache of old image
    )
    return result['secure_url']

def delete_image(object_key):
    cloudinary.uploader.destroy(object_key)