import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent


# function that store the certificates in the right folder
def handle_uploaded_file(f, name_thing, name_file):
    if not (os.path.exists(os.path.join(BASE_DIR, 'certificates/' + name_thing))):
        os.mkdir(os.path.join(BASE_DIR, 'certificates/' + name_thing))
    with open(os.path.join(BASE_DIR, 'certificates/' + name_thing + '/' + name_file), 'wb+') as destination:
        for chunk in f.chunks():
            destination.write(chunk)


# Delete certificate folder and files
def handle_deletion(name_thing):
    if os.path.exists(os.path.join(BASE_DIR, 'certificates/' + name_thing)):
        os.remove(os.path.join(BASE_DIR, 'certificates/' + name_thing+'/', "Private-private.pem.key"))
        os.remove(os.path.join(BASE_DIR, 'certificates/' + name_thing + '/', "Thing-certificate.pem.crt"))
        os.rmdir(os.path.join(BASE_DIR, 'certificates/' + name_thing))