import cv2

rtsp_url = "rtsp://admin:fkqxk010@192.168.1.101:554/Streaming/Channels/101"


cap = cv2.VideoCapture(rtsp_url, cv2.CAP_FFMPEG)
cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)
while True:
    ret, frame = cap.read()

    cv2.imshow("RTSP Stream", frame)
    cv2.waitKey(0)
cap.release()
cv2.destroyAllWindows()