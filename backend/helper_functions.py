ALLOWED_EXTENSIONS = {'pdf', 'png', 'jpg', 'jpeg'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


def rename_keys_in_place(data: dict, key_map: dict):
    for old_key, new_key in key_map.items():
        if old_key in data:
            data[new_key] = data.pop(old_key)
    return data