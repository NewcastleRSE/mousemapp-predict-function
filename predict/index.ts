import { AzureFunction, Context, HttpRequest } from "@azure/functions"
import parseMultipartFormData from '@anzp/azure-function-multipart'

interface Metadata {
    name: string
    room: string
    cage: string
    mouseID: string
    dateTime: Date
}

const httpTrigger: AzureFunction = async function (context: Context, req: HttpRequest): Promise<void> {
    const { fields, files } = await parseMultipartFormData(req)
    context.log('HTTP trigger function processed a request.')

    const requiredProperties = ['name', 'room', 'cage', 'mouseID']

    const properties = fields.map(field => field.name),
          images = files.map(file => file.filename)

    const hasAllProperties = requiredProperties.every(property => properties.includes(property))

    if(hasAllProperties) {

        const metadata: Metadata = {
            name: fields.find(field => field.name === 'name').value,
            room: fields.find(field => field.name === 'room').value,
            cage: fields.find(field => field.name === 'cage').value,
            mouseID: fields.find(field => field.name === 'mouseID').value,
            dateTime: new Date()
        }

        const response = {
            name: metadata.name,
            room: metadata.room,
            cage: metadata.cage,
            mouseID: metadata.mouseID,
            dateTime: metadata.dateTime,
            // prediction: meanprediction
        }

        context.res = {
            body: response
        }
    }
    else {
        context.res = {
            status: 400,
            body: `Invalid input. Request must include ${requiredProperties.toString()}`
        } 
    }

};

export default httpTrigger;