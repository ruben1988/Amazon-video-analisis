#Copyright 2018 Amazon.com, Inc. or its affiliates. All Rights Reserved.
#PDX-License-Identifier: MIT-0 (For details, see https://github.com/awsdocs/amazon-rekognition-developer-guide/blob/master/LICENSE-SAMPLECODE.)

import boto3
import json
import sys


class VideoDetect:
    jobId = ''
    rek = boto3.client('rekognition')
    queueUrl = ''
    roleArn = ''
    topicArn = ''
    bucket = 'videopruebas12'
    video = 'Bond.mp4'

    def main(self):

        jobFound = False
        sqs = boto3.client('sqs')


        #=====================================
        response = self.rek.start_label_detection(Video={'S3Object': {'Bucket': self.bucket, 'Name': self.video}},
                                         NotificationChannel={'RoleArn': self.roleArn, 'SNSTopicArn': self.topicArn})
        #print(response)
        #=====================================
        print('Start Job Id: ' + response['JobId'])
        dotLine=0
        while jobFound == False:
            sqsResponse = sqs.receive_message(QueueUrl=self.queueUrl, MessageAttributeNames=['ALL'],
                                          MaxNumberOfMessages=10)
            #print(sqsResponse)
            if sqsResponse:
                
                if 'Messages' not in sqsResponse:
                    if dotLine<20:
                        #print('.', end='')
                        dotLine=dotLine+1
                    else:
                        print()
                        dotLine=0    
                    sys.stdout.flush()
                    continue

                for message in sqsResponse['Messages']:
                    notification = json.loads(message['Body'])
                    rekMessage = json.loads(notification['Message'])
                    print("Hola que tal")
                    print(rekMessage['JobId'])
                    print(rekMessage['Status'])
                    if str(rekMessage['JobId']) == response['JobId']:
                        print('Matching Job Found:' + rekMessage['JobId'])
                        jobFound = True
                        #=============================================
                        self.GetResultsLabels(rekMessage['JobId'])
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


    def GetResultsLabels(self, jobId):
        maxResults = 10
        paginationToken = ''
        finished = False

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
                if (labelDetection['Label']['Name'] =="Gun"):
                    print("\n")
                    print("Label Name: ", labelDetection['Label']['Name'])
                    print("Label Confidence: ", labelDetection['Label']['Confidence'])
                    print("Label Timestamp: ",str(labelDetection['Timestamp']))
                    print("\n")

            if 'NextToken' in response:
                paginationToken = response['NextToken']
            else:
                finished = True


if __name__ == "__main__":

    analyzer=VideoDetect()
    analyzer.main()