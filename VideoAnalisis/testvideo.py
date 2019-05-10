import boto3
import json
import sys


class VideoDetect:
    jobId = ''
    rek = boto3.client('rekognition', region_name='eu-west-1')
    roleArn = ''
    queueUrl = ''
    topicArn = ''
    bucket = ''
    video = ''

    def main(self,arg):
        if (arg[1] == "label" or arg[1] == "position"):
            self.rek.start_label_detection(Video={'S3Object': {'Bucket': self.bucket, 'Name': self.video}},
                                                  NotificationChannel={'RoleArn': self.roleArn,
                                                                       'SNSTopicArn': self.topicArn})
        if (arg[1] == "celeb"):
            self.rek.start_celebrity_recognition(Video={'S3Object': {'Bucket': self.bucket, 'Name': self.video}},
                                                            NotificationChannel={'RoleArn': self.roleArn,
                                                                                 'SNSTopicArn': self.topicArn})

        sqs = boto3.client('sqs', region_name='eu-west-1')


        sqsResponse = sqs.receive_message(QueueUrl=self.queueUrl, MessageAttributeNames=['ALL'],
                                      MaxNumberOfMessages=10)
        if sqsResponse:
            for message in sqsResponse['Messages']:

                notification = json.loads(message['Body'])
                rekMessage = json.loads(notification['Message'])
                print(rekMessage['JobId'])
                print(rekMessage['Status'])
                #=============================================
                if (arg[1] == "label"):
                    self.GetResultsLabels(rekMessage['JobId'])
                if (arg[1] == "position"):
                    self.GetResultsBoundingBox(rekMessage['JobId'])
                if (arg[1] == "celeb"):
                    self.GetResultsCelebrities(rekMessage['JobId'])
                #=============================================

                sqs.delete_message(QueueUrl=self.queueUrl,
                               ReceiptHandle=message['ReceiptHandle'])

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

    analyzer=VideoDetect()
    analyzer.main(sys.argv)