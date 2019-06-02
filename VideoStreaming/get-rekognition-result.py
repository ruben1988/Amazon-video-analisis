#! /usr/bin/python
import boto3, time, subprocess, sys, json, cv2
import datetime

foundedNames = []

openCVPath = '/Users/ruben/opencv/haarcascades/'
faceCascadeFile = openCVPath + 'haarcascade_frontalface_alt2.xml'
eyeCascadeFile = openCVPath + 'haarcascade_eye_tree_eyeglasses.xml'
faceCascade = cv2.CascadeClassifier(faceCascadeFile)
eyeCascade = cv2.CascadeClassifier(eyeCascadeFile)


def actions(name):
	if not (name in foundedNames):
		foundedNames.append(name)
		subprocess.call(["python", "say_hi.py", name])
		#subprocess.call(["python", "sns-publish.py", name])
	else:
		print("Founded %d peoples, names" % len(foundedNames))

with open('config.json') as json_data_file:
	config = json.load(json_data_file)

region = config['region']
kinesisDataStream = config['kinesisDataStreamName']

kinesis = boto3.client('kinesis', region_name=region)
stream = kinesis.describe_stream(StreamName=kinesisDataStream)
shardId = stream['StreamDescription']['Shards'][0]['ShardId']
shardIterator = kinesis.get_shard_iterator(StreamName=kinesisDataStream,
									 ShardId=shardId,
									 ShardIteratorType="LATEST")
shard_it = shardIterator["ShardIterator"]

'''
FRAME_WIDTH = 640
FRAME_HEIGHT = 480

cap = cv2.VideoCapture(0)
cap.set(cv2.CAP_PROP_FRAME_WIDTH,FRAME_WIDTH)
cap.set(cv2.CAP_PROP_FRAME_HEIGHT,FRAME_HEIGHT)
'''


# draw bounding boxe around one face
def draw_bounding_box(cv_img, cv_img_width, cv_img_height, width, height, top, left, color):
	# calculate bounding box coordinates top-left - x,y, bottom-right - x,y
	width_pixels = int(width * cv_img_width)
	height_pixels = int(height * cv_img_height)
	left_pixel = int(left * cv_img_width)
	top_pixel = int(top * cv_img_height)
	cv2.rectangle(cv_img, (left_pixel, top_pixel), (left_pixel+width_pixels, top_pixel+height_pixels), color, 2)
	return cv_img


FRAME_WIDTH = 1280
FRAME_HEIGHT = 720

#vs = VideoStream(src=0).start()
#time.sleep(2.0)
cap = cv2.VideoCapture(0)

while True:

	ret, frame = cap.read()
	cap.set(3, FRAME_WIDTH)
	cap.set(4, FRAME_HEIGHT)
	image = frame

	if ret is False:
		break

	# draw the text and timestamp on the frame
	tsz = datetime.datetime.fromtimestamp(time.time()).strftime('%Y-%m-%d %H:%M:%S')
	cv2.putText(image, tsz, (10, frame.shape[0] - 10), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 1)


	try:
		recs = kinesis.get_records(ShardIterator=shard_it, Limit=1)
		shard_it = recs["NextShardIterator"]
		if len(recs['Records']) > 0:
			data = json.loads(recs['Records'][0]['Data'])
			if len(data['FaceSearchResponse']) > 0:
				#print(data['InputInformation']['KinesisVideo']['ServerTimestamp'])
				print('detect faces: %d' % len(data['FaceSearchResponse']))
				timestamp=str(data['InputInformation']['KinesisVideo']['ServerTimestamp'])
				cv2.putText(image, timestamp, (10, frame.shape[0] - 40), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 1)
				for faceSearchResponse in data['FaceSearchResponse']:
					print("Detectando caras")
					boundingBox = faceSearchResponse['DetectedFace']['BoundingBox']

					cv2.rectangle(frame,(int(boundingBox['Left'] * FRAME_WIDTH),int(boundingBox['Top'] * FRAME_HEIGHT)),
							(int((boundingBox['Left'] + boundingBox['Width']) * FRAME_WIDTH),
							int((boundingBox['Top'] + boundingBox['Height']) * FRAME_HEIGHT)),
							(255, 0, 0), 2)
					if len(faceSearchResponse['MatchedFaces']) > 0:
						print('match faces: %d' % len(faceSearchResponse['MatchedFaces']))
						#print("Texto o json de MatchedFaces")
						#print(faceSearchResponse['MatchedFaces'])
						#{u'Face': {u'BoundingBox': {u'Width': 0.460263, u'Top': 0.259856, u'Left': 0.261786, u'Height': 0.491053}, u'FaceId': u'e576250a-32c0-430b-a02b-1af62e7e634e', u'ExternalImageId': u'Ruben', u'Confidence': 100.0, u'ImageId': u'fea14003-bfc7-31a4-a5e5-effa1323f5dd'}, u'Similarity': 95.51174}
						for face in faceSearchResponse['MatchedFaces']:
							name = face['Face']['ExternalImageId']
							confidence = face['Face']['Confidence']
							boundingBox = face['Face']['BoundingBox']
							print("BoundingBox")
							print(face['Face']['BoundingBox'])
							#{u'Width': 0.460263, u'Top': 0.259856, u'Left': 0.261786, u'Height': 0.491053}

							width = boundingBox.get('Width')
							height = boundingBox.get('Height')
							left = boundingBox.get('Left')
							top = boundingBox.get('Top')

							width_pixels = int(width * FRAME_WIDTH)
							height_pixels = int(height * FRAME_HEIGHT)
							left_pixel = int(left * FRAME_WIDTH)
							top_pixel = int(top * FRAME_HEIGHT)
							print("puntos")
							print(width_pixels, height_pixels, left_pixel, top_pixel)
							xCenter = (left_pixel+width_pixels)/2
							yCenter = (top_pixel + height_pixels)/2
							print(xCenter,yCenter)
							cv2.putText(image, name, (xCenter, yCenter),cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)
							print('match face: %s confidence: %d' % (name, confidence))
							actions(name)
	except Exception as e:
		print(e.message)
		time.sleep(0.1)

	# Our operations on the frame come here
	gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

	faces = faceCascade.detectMultiScale(
		gray,
		scaleFactor=1.5,
		minNeighbors=5,
		minSize=(30, 30)
	)

	for (x, y, w, h) in faces:
		# Draw a rectangle around the faces
		cv2.rectangle(image, (x, y), (x + w, y + h), (0, 0, 255), 2)
		# Draw eyes
		roi_gray = gray[y:y + h, x:x + w]
		roi_color = image[y:y + h, x:x + w]
		eyes = eyeCascade.detectMultiScale(roi_gray)
		for (ex, ey, ew, eh) in eyes:
			cv2.rectangle(roi_color, (ex, ey), (ex + ew, ey + eh), (0, 0, 255), 2)


	cv2.imshow("Frame", image)
	key = cv2.waitKey(1) & 0xFF

	# if the `q` key was pressed, break from the loop
	if key == ord("q"):
		break
	# avoid ProvisionedThroughputExceededException
	time.sleep(0.2)

cv2.destroyAllWindows()
