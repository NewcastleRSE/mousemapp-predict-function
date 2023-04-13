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
CROP_SIZE = 224

def main(req: func.HttpRequest) -> func.HttpResponse:
    logging.info('Python HTTP trigger function processed a request.')

    metadata = req.form.to_dict()
    inputValidation = {}
    fileValidation = {}

    if not metadata.get('observerName'):
        inputValidation['observerName'] = 'An observer name is required'

    if not metadata.get('roomID'):
        inputValidation['roomID'] = 'A room ID is required'

    if not metadata.get('cageID'):
        inputValidation['cageID'] = 'A cage ID is required'

    if not metadata.get('mouseID'):
        inputValidation['mouseID'] = 'A mouse ID is required'

    if not req.files.get('image1') and not req.files.get('image2') and not req.files.get('image3'):
        inputValidation['images'] = 'An image of a mouse is required'

    if inputValidation:
        return func.HttpResponse(
            json.dumps({'errors': inputValidation}),
            status_code=415,
            headers={"Content-Type": "application/json"}
        )

    scores = []
    filemetadata = []

    for file in req.files.keys():

        image = Image.open(req.files[file])
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
            scores.append(score)

            filename, extension = os.path.splitext(req.files[file].filename)

            file_metadata = {
                "filename": filename + extension,
                "mimeType": req.files[file].mimetype,
                "bcs": str(score)
            }

            filemetadata.append(file_metadata)

            print({**metadata, **file_metadata})

            blob = BlobClient.from_connection_string(conn_str=CONN_STR, container_name=UPLOADS_CONTAINER_NAME, blob_name=str(uuid.uuid4()) + extension)
            blob.upload_blob(imgByteArr)
            blob.set_blob_metadata({**metadata, **file_metadata})

        else:
            fileValidation[file] = 'Invalid image detected'

        if fileValidation:
            return func.HttpResponse(
                json.dumps({'message': 'Invalid image detected'}),
                status_code=415,
                headers={"Content-Type": "application/json"}
            )
            

    metadata['files'] = filemetadata
    if len(scores) > 0:
        metadata['bcs'] = sum(scores)/len(scores)
    else:
       metadata['bcs'] = 0 

    return func.HttpResponse(
        json.dumps(metadata),
        status_code=200,
        headers={"Content-Type": "application/json"}
    )
