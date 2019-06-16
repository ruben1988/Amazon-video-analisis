import cv2
import boto3


# Setup
scale_factor = .15
green = (0, 255, 0)
red = (0, 0, 255)
frame_thickness = 2
FRAME_WIDTH = 1920
FRAME_HEIGHT = 1080


# Opens the Video file
cap = cv2.VideoCapture('/Users/ruben/Documents/videos/Bond.mp4')
rekognition = boto3.client('rekognition')


# create writer object
fileName = 'output.avi'  # change the file name if needed
imgSize = (FRAME_WIDTH, FRAME_HEIGHT)
frame_per_second = 24.0
writer = cv2.VideoWriter(fileName, cv2.VideoWriter_fourcc(*"MJPG"), frame_per_second,imgSize)

while(True):

    # Capture frame-by-frame
    ret, frame = cap.read()
    height, width, channels = frame.shape

    # Convert frame to jpg
    #small = cv2.resize(frame, (int(width * scale_factor), int(height * scale_factor)))
    ret, buf = cv2.imencode('.jpg', frame)

    # Detect celebrity in jpg
    faces = rekognition.recognize_celebrities(Image={'Bytes': buf.tobytes()})


    # Draw rectangle around faces
    for face in faces['CelebrityFaces']:
        print("\n")
        print(face)
        print("\n")
        if face['Face']:
            name = (face['Name']).encode('utf-8')
            boundingBox = face['Face']['BoundingBox']
            confidence = face['Face']['Confidence']
            width = boundingBox.get('Width')
            height = boundingBox.get('Height')
            left = boundingBox.get('Left')
            top = boundingBox.get('Top')
            width_pixels = int(width * FRAME_WIDTH)
            height_pixels = int(height * FRAME_HEIGHT)
            left_pixel = int(left * FRAME_WIDTH)
            top_pixel = int(top * FRAME_HEIGHT)

            cv2.rectangle(frame, (int(left * FRAME_WIDTH), int(top * FRAME_HEIGHT)),
                          (int((left + width) * FRAME_WIDTH),
                           int((top + height) * FRAME_HEIGHT)),
                          red, frame_thickness)
            xCenter = (left_pixel + width_pixels)/2
            yCenter = (top_pixel + height_pixels)/2

            cv2.putText(frame, name, (xCenter, yCenter), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)
            cv2.putText(frame, str(confidence), (xCenter, yCenter+30), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)

    # Display the resulting frame
    writer.write(frame)
    cv2.imshow('frame', frame)
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

# When everything done, release the capture
cap.release()
writer.release()
cv2.destroyAllWindows()
