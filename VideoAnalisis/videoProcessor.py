import boto3, json, sys, argparse, time


parser = argparse.ArgumentParser(description='video analisis with rekognition')
parser.add_argument('-l', '--label', action='store_true', help='label video analisis')
parser.add_argument('-c', '--celebrity', action='store_true', help='celebrity video analisis')
parser.add_argument('-b', '--position', action='store_true', help='person bounding box analisis')
parser.add_argument('-p', '--person', action='store_true', help='person Tracking analisis')


class VideoDetect:
    jobId = ''
    video = 'Bond.mp4'

    with open('config.json') as json_data_file:
        config = json.load(json_data_file)

    bucket = config['bucketName']
    region = config['region']
    iamRole = config['iamRole']
    sqsName = config['sqsRekognitionName']
    snsTopicName = config['snsTopicRekognitionName']

    # aws accountID
    stsClient = boto3.client('sts', region_name=region)
    accountID = stsClient.get_caller_identity()["Account"]
    roleArn = 'arn:aws:iam::' + accountID + ':role/' + iamRole
    topicArn = 'arn:aws:sns:' + region + ':' + accountID + ':' + snsTopicName
    queueUrl = 'https://sqs.' + region + '.amazonaws.com/' + accountID + '/' + sqsName
    rek = boto3.client('rekognition', region_name=region)

    sns = boto3.client('sns', region_name=region)


    def main(self,arg):

        jobFound = False

        if arg.person:
            response=self.rek.start_person_tracking(Video={'S3Object': {'Bucket': self.bucket, 'Name': self.video}},
                                                  NotificationChannel={'RoleArn': self.roleArn,
                                                                       'SNSTopicArn': self.topicArn})

        if arg.label or arg.position:
            response=self.rek.start_label_detection(Video={'S3Object': {'Bucket': self.bucket, 'Name': self.video}},
                                                  NotificationChannel={'RoleArn': self.roleArn,
                                                                       'SNSTopicArn': self.topicArn})

        if arg.celebrity:
            response=self.rek.start_celebrity_recognition(Video={'S3Object': {'Bucket': self.bucket, 'Name': self.video}},
                                                            NotificationChannel={'RoleArn': self.roleArn,
                                                                                 'SNSTopicArn': self.topicArn})
            #print(response)
        sqs = boto3.client('sqs', region_name=self.region)



        print('Start Job Id: ' + response['JobId'])
        dotLine=0



        while jobFound == False:


            sqsResponse = sqs.receive_message(QueueUrl=self.queueUrl, MessageAttributeNames=['ALL'],
                                      MaxNumberOfMessages=10)

            if sqsResponse:
                #print(sqsResponse)
                #print("Waiting for connection")
                if 'Messages' not in sqsResponse:
                    if dotLine < 30:
                        #print('.')
                        dotLine = dotLine + 1
                    else:
                        print("sorry waiting ...")
                        dotLine = 0
                        print(sqsResponse)
                    sys.stdout.flush()
                    continue
                else:
                    print(sqsResponse['Messages'])

                for message in sqsResponse['Messages']:

                    notification = json.loads(message['Body'])
                    rekMessage = json.loads(notification['Message'])
                    print(rekMessage['JobId'])
                    print(rekMessage['Status'])
                    if str(rekMessage['JobId']) == response['JobId']:
                        print('Matching Job Found:' + rekMessage['JobId'])
                        jobFound = True
                        #=============================================
                        if (arg.label):
                            self.GetResultsLabels(rekMessage['JobId'])
                        if (arg.position):
                            self.GetResultsBoundingBox(rekMessage['JobId'])
                        if (arg.person):
                            self.GetResultsPersonTracking(rekMessage['JobId'])
                        if (arg.celebrity):
                            self.GetResultsCelebrities(rekMessage['JobId'])
                        #=============================================

                        sqs.delete_message(QueueUrl=self.queueUrl,
                                       ReceiptHandle=message['ReceiptHandle'])
                    else:
                        print("Job didn't match:" +
                              str(rekMessage['JobId']) + ' : ' + str(response['JobId']))
                        # Delete the unknown message. Consider sending to dead letter queue
                    sqs.delete_message(QueueUrl=self.queueUrl,
                                       ReceiptHandle=message['ReceiptHandle'])

        print('done')


    def GetResultsBoundingBox(self, jobId):
        maxResults = 10
        paginationToken = ''
        finished = False

        print("Label detection: \n")

        while finished == False:
            response = self.rek.get_label_detection(JobId=jobId,
                                            MaxResults=maxResults,
                                            NextToken=paginationToken,
                                            SortBy='TIMESTAMP')

            for labelDetection in response['Labels']:
                if (labelDetection['Label']['Name'] =="Person"):
                    print("\n")
                    print("Label Name: ", labelDetection['Label']['Name'])
                    print("Label Confidence: ", labelDetection['Label']['Confidence'])
                    print("People Detected on a frame: ")
                    for instance in labelDetection['Label']['Instances']:
                        print("Person Detected in position: ")
                        print(instance['BoundingBox'])
                    print("Label Timestamp: ",str(labelDetection['Timestamp']))
                    print("\n")

            if 'NextToken' in response:
                paginationToken = response['NextToken']
            else:
                finished = True

    def GetResultsPersonTracking(self, jobId):
        maxResults = 10
        paginationToken = ''
        finished = False
        print("Person Tracking: \n")
        while finished == False:
            response = self.rek.get_person_tracking(JobId=jobId,
                                                          MaxResults=maxResults,
                                                          NextToken=paginationToken,
                                                            SortBy='TIMESTAMP')

            print(response['VideoMetadata']['Codec'])
            print(str(response['VideoMetadata']['DurationMillis']))
            print(response['VideoMetadata']['Format'])
            print(response['VideoMetadata']['FrameRate'])

            for personRecognition in response['Persons']:
                print('Person Index: ' +
                      str(personRecognition['Person']['Index']))
                print('Timestamp: ' + str(personRecognition['Timestamp']))
                print('BoundingBox: ' + str(personRecognition['Person']['BoundingBox']))

            if 'NextToken' in response:
                paginationToken = response['NextToken']
            else:
                finished = True

    def GetResultsCelebrities(self, jobId):
        maxResults = 10
        paginationToken = ''
        finished = False
        print("Celebrity detection: \n")

        while finished == False:
            response = self.rek.get_celebrity_recognition(JobId=jobId,
                                                          MaxResults=maxResults,
                                                          NextToken=paginationToken)

            print(response['VideoMetadata']['Codec'])
            print(str(response['VideoMetadata']['DurationMillis']))
            print(response['VideoMetadata']['Format'])
            print(response['VideoMetadata']['FrameRate'])

            for celebrityRecognition in response['Celebrities']:
                print('Celebrity: ' +
                      str(celebrityRecognition['Celebrity']['Name']))
                print('Timestamp: ' + str(celebrityRecognition['Timestamp']))
                print()

            if 'NextToken' in response:
                paginationToken = response['NextToken']
            else:
                finished = True

    def GetResultsLabels(self, jobId):
        maxResults = 10
        paginationToken = ''
        finished = False

        print("Label detection: \n")

        while finished == False:
            response = self.rek.get_label_detection(JobId=jobId,
                                                    MaxResults=maxResults,
                                                    NextToken=paginationToken,
                                                    SortBy='TIMESTAMP')

            '''print("Codec: ", response['VideoMetadata']['Codec'])
            print("DurationMillis: ", str(response['VideoMetadata']['DurationMillis']))
            print("Format: ", response['VideoMetadata']['Format'])
            print("FrameRate: ", response['VideoMetadata']['FrameRate'])'''

            for labelDetection in response['Labels']:
                if (labelDetection['Label']['Name'] == "Gun"):
                    print("\n")
                    print("Label Name: ", labelDetection['Label']['Name'])
                    print("Label Confidence: ", labelDetection['Label']['Confidence'])
                    print("Label Timestamp: ", str(labelDetection['Timestamp']))
                    print("\n")

            if 'NextToken' in response:
                paginationToken = response['NextToken']
            else:
                finished = True


if __name__ == "__main__":
    if len(sys.argv)==1:
        parser.print_help()
        sys.exit(1)

    args = parser.parse_args()

    analyzer=VideoDetect()
    analyzer.main(args)