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
from azure.storage.blob import ContainerClient

import azure.functions as func

ACCOUNT_NAME = os.getenv('ACCOUNT_NAME')
ACCOUNT_KEY = os.getenv('ACCOUNT_KEY')
UPLOADS_CONTAINER_NAME = 'uploads'
MODEL_CONTAINER_NAME = 'model'
CONN_STR = "DefaultEndpointsProtocol=https;AccountName=" + ACCOUNT_NAME + ";AccountKey=" + ACCOUNT_KEY + ";EndpointSuffix=core.windows.net"
CROP_SIZE=224

def main(req: func.HttpRequest) -> func.HttpResponse:
    logging.info('Python HTTP trigger function processed a request.')

    container = ContainerClient.from_connection_string(conn_str=CONN_STR, container_name=MODEL_CONTAINER_NAME)
    modelBlobs = container.list_blobs()

    print(os.getcwd() + "/model")

    for blob in modelBlobs:
        blobClient = container.get_blob_client(blob)

        print(os.getcwd() + "/predict/model/" + blob.name)

        if os.path.isfile(os.getcwd() + "/predict/model/" + blob.name):
            print("Model exists locally")
        else:
            print("Model does not exist locally, download from Azure")
            with open(os.getcwd() + "/model", "wb") as file:
                download_stream = blobClient.download_blob()
                file.write(download_stream.readall())

    metadata = {
        "name": req.form['name'],
        "room": req.form['room'],
        "cage": req.form['cage'],
        "mouseID": req.form['mouseID']
    }

    for file in req.files.values():

        image = Image.open(file)
        imgByteIO = io.BytesIO()
        image.save(imgByteIO, format=image.format)
        imgByteArr = imgByteIO.getvalue()

        test_transforms = transforms.Compose(
            [
                transforms.Resize((CROP_SIZE, CROP_SIZE)),
                transforms.ToTensor(),
                transforms.Normalize([0.485], [0.229]),
            ]
        )

        device = torch.device("cuda:0" if torch.cuda.is_available() else "cpu")

        model_ae = torch.load(os.getcwd() + "/predict/model/model_ae.pt", map_location=torch.device("cpu"))
        model_ae.to(device)
        model_ae.eval()
        criterion = nn.MSELoss()

        model_pred = torch.load(os.getcwd() + "/predict/model/model_pytorch_alexnet.pt", map_location=torch.device("cpu"))
        model_pred.to(device)
        model_pred.eval()

        img = image.convert("RGB")
        img = test_transforms(img).to(device)
        img = torch.unsqueeze(img, 0)

        recon = model_ae(img)

        loss_ae = criterion(img, recon).item()

        if loss_ae < 0.0400:
            pred = model_pred(img)
            prob_softmax = torch.softmax(pred, dim=1)
            _, standard_prediction = torch.max(prob_softmax, 1)
            score = standard_prediction.detach().cpu().numpy()[0] + 2
            print("BCS:", score)

            filename, extension = os.path.splitext(file.filename)

            metadata['filename'] = filename + extension
            metadata['mimeType'] = file.mimetype
            metadata['bcs'] = str(score)

            blob = BlobClient.from_connection_string(conn_str=CONN_STR, container_name=UPLOADS_CONTAINER_NAME, blob_name=str(uuid.uuid4()) + extension)
            blob.upload_blob(imgByteArr)
            blob.set_blob_metadata(metadata)

        else:
            print("please use a different image")

    return func.HttpResponse(
        json.dumps(metadata),
        status_code=200,
        headers={"Content-Type": "application/json"}
    )
