# Mouse MApp Predict Function
A HTTP Trigger Azure Function for running new images through the [MouseMApp Model](https://github.com/NewcastleRSE/Mouse_MApp_model).

## About

The function is configured for use via a HTTP Post request, taking in multipart form data and then running the posted file against the Mouse MApp classifier model. On completion the image is uploaded to Azure Storage and tagged with the metadata accompanying the initial post request.

### Project Team
Matt Leach, Newcastle University  ([matthew.leach@ncl.ac.uk](mailto:matthew.leach@ncl.ac.uk))   
Satnam Dlay, Newcastle University  ([rsatnam.dlay@newcastle.ac.uk](mailto:rsatnam.dlay@newcastle.ac.uk))

### RSE Contact
Nik Khadijah Nik Aznan 
RSE Team  
Newcastle University  
([nik.nik-aznan@newcastle.ac.uk](mailto:nik.nik-aznan@newcastle.ac.uk))  

## Built With

The application is a native Azure Function, so requires the Azure Functions Core Tools to be installed for local development.

[Azure Function Core Tools](https://github.com/Azure/azure-functions-core-tools)  

## Getting Started

### Prerequisites

This guide assumes both Python 3.9 and Azure Functions Core Tools are installed. The files `model_ae.pt` and `model_pytorch_alexnet.pt` must be present in the `model` container in the storage account.

### Installation

Start a new Python virtual environment.

```bash
python -m venv .venv
```

Install the dependencies

```bash
pip install -r requirements.txt
```
Export the required environment variables, both of which can be obtained from the Azure Storage account via the Azure Portal.

```bash
export ACCOUNT_NAME=XXXXXXXXXXX
export ACCOUNT_KEY=XXXXXXXXXXX
```

### Running Locally

To start the function locally run

```bash
func start
```

## Deployment

Deployment is handled via a GitHub workflow that builds and deploys the function directly to Azure.

### Terraform

All of the production resources required are configured via a Terraform script in the `terraform` directory. Running `terraform apply` will create the resource group, storage, app service and function needed.

### Production

Any `push` on the main branch will trigger a build and release of the function. As part of the build process the model files are pulled into the function directory from the storage container, so these files **must** be there for the build to complete.
 
## Usage

Any links to production environment, video demos and screenshots.

## Roadmap

- [x] Initial Research  
- [x] Minimum viable product  
- [x] Alpha Release  
- [x] Feature-Complete Release  

## Contributing

### Main Branch
Protected and can only be pushed to via pull requests. Should be considered stable and a representation of production code.

### Dev Branch
Should be considered fragile, code should compile and run but features may be prone to errors.

### Feature Branches
A branch per feature being worked on.

https://nvie.com/posts/a-successful-git-branching-model/

## License

[![License: GPL v3](https://img.shields.io/badge/License-GPLv3-blue.svg)](https://www.gnu.org/licenses/gpl-3.0)