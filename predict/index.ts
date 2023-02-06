import { AzureFunction, Context, HttpRequest } from "@azure/functions"
import parseMultipartFormData from '@anzp/azure-function-multipart'
import * as tf from '@tensorflow/tfjs'

interface Metadata {
    name: string
    room: string
    cage: string
    mouseID: string
    dateTime: Date
}

interface MultipartFile {
    name: string
    bufferFile: Buffer
    filename: string
    encoding: string
    mimeType: string
}

let model: any

const tensorflowLoadModel: Function = async(modelPath: string) => {
    model = await tf.loadLayersModel(modelPath)
}

const predict: Function = async(files: MultipartFile[]) => {

    const predictions = []

    for(const file of files) {
        let decoded

        if(file.mimeType === 'image/jpeg') {
            decoded = tf.node.decodeJpeg(file.bufferFile)
        }
        else if(file.mimeType === 'image/png') {
            decoded = tf.node.decodePng(file.bufferFile).slice([0], [-1, -1, 3])
        }
        else {
            throw new EvalError('Image is not a JPG or PNG')
        }

        // Resize image to correct sizing of 224, 224, 3 (size, size, colour channel)
        
        let resized = tf.image.resizeBilinear(decoded, [224, 224])

        // Covert to RGB if Greyscale
        let colourImg = resized.shape[resized.shape.length - 1] === 1 ? tf.image.grayscaleToRGB(resized) : resized
        let expandedImg = tf.expandDims(colourImg, 0)

        //Predict
        const prediction = await model.predict(expandedImg)

        /* prediction is -2 compared to the real score for the mouse
        this is due to python starting at 0 not 1 and there currently being no ability for the app to score a 1
        When the app can score 1s, this will need to be altered to +1 instead of +2
        */
        predictions.push(prediction.argMax(1).dataSync()[0] + 2)
    }

    if(predictions.length > 0) {
        let total = 0

        for (let prediction of predictions){
          total = total + parseFloat(prediction)
        }

        return total/predictions.length
    }
    else {
        return null
    }
}

const httpTrigger: AzureFunction = async function (context: Context, req: HttpRequest): Promise<void> {
    const { fields, files } = await parseMultipartFormData(req)
    await tensorflowLoadModel(`file://${context.executionContext.functionDirectory}/assets/trainedModel/model.json`)

    const requiredProperties = ['name', 'room', 'cage', 'mouseID']

    const properties = fields.map(field => field.name),
          images = files.map(file => file.filename)

    const hasAllProperties = requiredProperties.every(property => properties.includes(property)),
          hasImages = images.length > 0

    if(hasAllProperties && hasImages) {

        const metadata: Metadata = {
            name: fields.find(field => field.name === 'name').value,
            room: fields.find(field => field.name === 'room').value,
            cage: fields.find(field => field.name === 'cage').value,
            mouseID: fields.find(field => field.name === 'mouseID').value,
            dateTime: new Date()
        }

        try {
            const response = {
                name: metadata.name,
                room: metadata.room,
                cage: metadata.cage,
                mouseID: metadata.mouseID,
                dateTime: metadata.dateTime,
                prediction: await predict(files)
            }
    
            context.res = {
                body: response
            }
        }
        catch (err: any) {
            let errorMessage
            
            if (err instanceof EvalError) {
                errorMessage = err.message
            } else {
                errorMessage = err.message
            }

            context.res = {
                status: 400,
                body: errorMessage
            }
        }
    }
    else {
        context.res = {
            status: 400,
            body: `Invalid input. Request must include ${requiredProperties.join(', ')} and at least 1 image.`
        } 
    }
}

export default httpTrigger