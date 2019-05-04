import boto3
import json
import argparse
import sys

parser = argparse.ArgumentParser(description='video stream processor helper for face recognition')
parser.add_argument('-c', '--create', action='store_true', help='create video stream processor')
parser.add_argument('-s', '--start', action='store_true', help='start video stream processor')
parser.add_argument('-q', '--stop', action='store_true', help='stop video stream processor')
parser.add_argument('-d', '--delete', action='store_true', help='delete video stream processor')


# inital
def createStreamProcessorHelper(streamProcessor, kinesisVideoStreamName, kinesisDataStream, collectionId, iamRole):

    # aws accountID
    stsClient = boto3.client('sts', region_name=region)
    accountID = stsClient.get_caller_identity()["Account"]

    # Get KinesisVideoStream Arn
    kvClient = boto3.client('kinesisvideo', region_name=region)
    kinesisVideoStreamArn = kvClient.describe_stream(StreamName=kinesisVideoStreamName)['StreamInfo']['StreamARN']

    #kinesisVideoStreamArn ="arn:aws:kinesisvideo:us-west-2:318089925419:stream/appVideoStream-videoFaceRek/1556876387219"
    kinesisDataStreamArn = 'arn:aws:kinesis:' + region + ':' + accountID + ':stream/' + kinesisDataStream
    roleArn = 'arn:aws:iam::' + accountID + ':role/' + iamRole
    #roleArn = "arn:aws:iam::318089925419:role/appRole-videoFaceRek"
    createStreamProcessor(streamProcessor, kinesisVideoStreamArn, kinesisDataStreamArn, collectionId, roleArn)


def createStreamProcessor(streamProcessor, kinesisVideoStreamArn, kinesisDataStreamArn, collectionId, roleArn):
    response = rekClient.create_stream_processor(
        Input={
            'KinesisVideoStream': {
                'Arn': kinesisVideoStreamArn
            }
        },
        Output={
            'KinesisDataStream': {
                'Arn': kinesisDataStreamArn
            }
        },
        Name=streamProcessor,
        Settings={
            'FaceSearch': {
                'CollectionId': collectionId,
                'FaceMatchThreshold': 70.0
            }
        },
        RoleArn=roleArn
    )
    print(response)

def startStreamProcessor(streamProcessor):
    response = rekClient.start_stream_processor(
        Name=streamProcessor
    )
    print(response)

def stopStreamProcess(streamProcessor):
    response = rekClient.stop_stream_processor(
        Name=streamProcessor
    )
    print(response)

def delStreamProcess(streamProcessor):
    response = rekClient.delete_stream_processor(
        Name=streamProcessor
    )
    print(response)

if __name__ == '__main__':
    if len(sys.argv)==1:
        parser.print_help()
        sys.exit(1)

    args = parser.parse_args()

    with open('config.json') as json_data_file:
        config = json.load(json_data_file)

    # configuration global variable
    region = config['region']
    kinesisVideoStreamName = config['kinesisVideoStreamName']
    kinesisDataStream = config['kinesisDataStreamName']
    streamProcessor = config['streamProcessor']
    collectionId = config['collectionId']
    iamRole = config['iamRole']

    rekClient = boto3.client('rekognition', region_name=region)

    if (args.create):
        createStreamProcessorHelper(streamProcessor, kinesisVideoStreamName, kinesisDataStream, collectionId, iamRole)
    elif (args.start):
        startStreamProcessor(streamProcessor)
    elif (args.stop):
        stopStreamProcess(streamProcessor)
    elif (args.delete):
        delStreamProcess(streamProcessor)
