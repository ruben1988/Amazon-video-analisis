import boto3, botocore, argparse, sys, json


parser = argparse.ArgumentParser(description='create video analisis with rekognition')
parser.add_argument('-c', '--create', action='store_true', help='create SNS, SQS & bucket')
parser.add_argument('-d', '--delete', action='store_true', help='delete SNS, SQS & bucket')


def createSNSTopic(snsTopicName):
    try:
        response = clientsns.create_topic(Name=snsTopicName)
        print(response)
    except botocore.exceptions.ClientError as e:
        print("Error: {0}".format(e))


def createSQS(sqsName):
    try:
        response = clientsqs.create_queue(QueueName=sqsName)
        print(response)
    except botocore.exceptions.ClientError as e:
        print("Error: {0}".format(e))


def createBucketS3(bucketname):
    try:
        response = s3_client.create_bucket(Bucket=bucketname,
            CreateBucketConfiguration={'LocationConstraint': region})
        print(response)
    except botocore.exceptions.ClientError as e:
        print("Error: {0}".format(e))


def susbcribeSQS(snsTopicName,sqsName):
    try:
        stsClient = boto3.client('sts')
        accountID = stsClient.get_caller_identity()["Account"]
        sns_topic_arn = 'arn:aws:sns:' + region + ':' + accountID + ':' + snsTopicName
        sqs_queue_arn = 'arn:aws:sqs:' + region + ':' + accountID + ':' + sqsName
        response = clientsns.subscribe(
            TopicArn=sns_topic_arn,
            Protocol='sqs',
            Endpoint=sqs_queue_arn
        )
        print(response)

        sqsUrl = 'https://sqs.' + region + '.amazonaws.com/' + accountID + '/' + sqsName

        response = clientsqs.add_permission(
            QueueUrl=sqsUrl,
            Label='videoSendMessage',
            AWSAccountIds=[
                accountID,
            ],
            Actions=[
                'SendMessage',
            ]
        )
        print(response)
    except botocore.exceptions.ClientError as e:
        print("Error: {0}".format(e))


def unsubscribeSQS(snsTopicName):
    try:
        response = clientsns.unsubscribe(
            SubscriptionArn=clientsns.list_subscriptions()["Subscriptions"][0]["SubscriptionArn"]
        )
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


def deleteSQS(sqsName):
    try:
        stsClient = boto3.client('sts')
        accountID = stsClient.get_caller_identity()["Account"]
        sqsUrl = 'https://sqs.' + region + '.amazonaws.com/' + accountID + '/' + sqsName
        response = clientsqs.delete_queue(QueueUrl=sqsUrl)
        print(response)
    except botocore.exceptions.ClientError as e:
        print("Error: {0}".format(e))


def deleteBucketS3(bucketName):
    try:
        response = s3_client.Bucket(bucketName).objects.delete()
        print(response)
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

    snsTopicName = config['snsTopicRekognitionName']
    clientsns = boto3.client('sns', region_name=region)

    sqsName = config['sqsRekognitionName']
    clientsqs = boto3.client('sqs', region_name=region)

    bucketName = config['bucketName']
    s3_client = boto3.client('s3')



    if (args.create):
        createSNSTopic(snsTopicName)
        createSQS(sqsName)
        #createBucketS3(bucketName)
        susbcribeSQS(snsTopicName,sqsName)
    elif (args.delete):
        deleteSNSTopic(snsTopicName)
        deleteSQS(sqsName)
        unsubscribeSQS(snsTopicName)
        #deleteBucketS3(bucketName)