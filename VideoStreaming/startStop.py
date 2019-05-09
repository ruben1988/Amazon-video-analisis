import boto3, botocore, argparse, sys, json


parser = argparse.ArgumentParser(description='create video stream analyzer')
parser.add_argument('-c', '--create', action='store_true', help='create SNS, kinesisVideoStream & kinesisDataStream')
parser.add_argument('-d', '--delete', action='store_true', help='delete SNS, kinesisVideoStream & kinesisDataStream')


def createSNSTopic(snsTopicName):
    try:
        response = clientsns.create_topic(Name=snsTopicName)
        print(response)
    except botocore.exceptions.ClientError as e:
        print("Error: {0}".format(e))


def createVideoStream(kinesisVideoStreamName):
    try:
        respone = clientVideo.create_stream(StreamName=kinesisVideoStreamName)
        print(respone)
    except botocore.exceptions.ClientError as e:
        print("Error: {0}".format(e))


def createDataStream(kinesisDataStreamName):
    try:
        response = clientKinesis.create_stream(
            StreamName=kinesisDataStreamName,
            ShardCount=1)
        print(response)
    except botocore.exceptions.ClientError as e:
        print("Error: {0}".format(e))

def deleteSNSTopic(snsTopicName):
    try:
        stsClient = boto3.client('sts')
        accountID = stsClient.get_caller_identity()["Account"]
        topicArn = 'arn:aws:sns:' + region + ':' + accountID + ':' + snsTopicName
        response = clientsns.delete_topic(TopicArn=topicArn)
        print(response)
    except botocore.exceptions.ClientError as e:
        print("Error: {0}".format(e))

def deleteDataStream(kinesisDataStreamName):
    try:
        response = clientKinesis.delete_stream(
            StreamName=kinesisDataStreamName
        )
        print (response)
    except botocore.exceptions.ClientError as e:
        print("Error: {0}".format(e))

def deleteVideoStream(kinesisVideoStreamName):
    try:
        kinesisVideoStreamArn = clientVideo.describe_stream(StreamName=kinesisVideoStreamName)['StreamInfo']['StreamARN']
        response = clientVideo.delete_stream(
            StreamARN=kinesisVideoStreamArn
        )
        print (response)
    except botocore.exceptions.ClientError as e:
        print("Error: {0}".format(e))


if __name__ == '__main__':
    if len(sys.argv)==1:
        parser.print_help()
        sys.exit(1)

    args = parser.parse_args()
    with open('config.json') as json_data_file:
        config = json.load(json_data_file)

    region = config['region']

    snsTopicName = config['snsTopicName']
    clientsns = boto3.client('sns', region_name=region)

    kinesisVideoStreamName = config['kinesisVideoStreamName']
    clientVideo = boto3.client('kinesisvideo', region_name=region)

    kinesisDataStreamName = config['kinesisDataStreamName']
    clientKinesis = boto3.client('kinesis', region_name=region)


    if (args.create):
        createSNSTopic(snsTopicName)
        createVideoStream(kinesisVideoStreamName)
        createDataStream(kinesisDataStreamName)
    elif (args.delete):
        deleteSNSTopic(snsTopicName)
        deleteVideoStream(kinesisVideoStreamName)
        deleteDataStream(kinesisDataStreamName)