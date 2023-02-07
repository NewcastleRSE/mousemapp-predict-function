import logging
import io
import os
import json
import torch
from torch import nn
from torchvision import transforms
import uuid
from PIL import Image
from azure.storage.blob import BlobServiceClient,BlobClient

import azure.functions as func

ACCOUNT_NAME = os.getenv('ACCOUNT_NAME')
ACCOUNT_KEY = os.getenv('ACCOUNT_KEY')
CONTAINER_NAME = 'uploads'
CONN_STR = "DefaultEndpointsProtocol=https;AccountName=" + ACCOUNT_NAME + ";AccountKey=" + ACCOUNT_KEY + ";EndpointSuffix=core.windows.net"
CROP_SIZE=224

def main(req: func.HttpRequest) -> func.HttpResponse:
    logging.info('Python HTTP trigger function processed a request.')

    
    test_transforms = transforms.Compose(
        [
            transforms.Resize((crop_size, crop_size)),
            transforms.ToTensor(),
            transforms.Normalize([0.485], [0.229]),
        ]
    )

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

        blob = BlobClient.from_connection_string(conn_str=CONN_STR, container_name=CONTAINER_NAME, blob_name=str(uuid.uuid4()) + extension)
        blob.upload_blob(imgByteArr)
        blob.set_blob_metadata(metadata)

    return func.HttpResponse(
        json.dumps(metadata),
        status_code=200,
        headers={"Content-Type": "application/json"}
    )
