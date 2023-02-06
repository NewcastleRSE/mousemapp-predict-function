import logging
import io
import os
import json
import time
import uuid
from PIL import Image
from azure.storage.blob import BlobServiceClient,BlobClient
from dotenv import dotenv_values

import azure.functions as func

config = dotenv_values(".env")

def main(req: func.HttpRequest) -> func.HttpResponse:
    logging.info('Python HTTP trigger function processed a request.')

    metadata = {
        "name": req.form['name'],
        "room": req.form['room'],
        "cage": req.form['cage'],
        "mouseID": req.form['mouseID']
    }

    for file in req.files.values():
        filename, extension = os.path.splitext(file.filename)

        metadata['filename'] = filename + extension
        metadata['mimeType'] = file.mimetype

        image = Image.open(file)
        imgByteIO = io.BytesIO()
        image.save(imgByteIO, format=image.format)
        imgByteArr = imgByteIO.getvalue()

        blob = BlobClient.from_connection_string(conn_str=config['conn_str'], container_name=config['container_name'], blob_name=str(uuid.uuid4()) + extension)
        blob.upload_blob(imgByteArr)
        blob.set_blob_metadata(metadata)

    return func.HttpResponse(
        json.dumps(metadata),
        status_code=200,
        headers={"Content-Type": "application/json"}
    )
