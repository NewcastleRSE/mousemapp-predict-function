FROM mcr.microsoft.com/azure-functions/node:4-node16
ENV AzureWebJobsScriptRoot=/home/site/wwwroot
ENV AzureFunctionsJobHost__Logging__Console__IsEnabled=true
COPY . /home/site/wwwroot

WORKDIR /home/site/wwwroot

RUN npm install -g yarn

RUN yarn install

RUN yarn build