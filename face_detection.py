import cv2

def face_detection(path):
    face_cascade=cv2.CascadeClassifier("haarcascade_frontalface_alt.xml")
    image = cv2.imread(path)           #读取图片
    gray = cv2.cvtColor(image,cv2.COLOR_BGR2GRAY)  #灰度转换
    faces = face_cascade.detectMultiScale(         #探测人脸
        gray,
        scaleFactor = 1.15,
        minNeighbors = 5,
        minSize = (5,5),
        )
    print("发现{0}个人脸！".format(len(faces)))

    for(x,y,w,h) in faces:
        cv2.rectangle(image,(x,y),(x+w,y+h),(0,255,0),2)

    # cv2.imshow("Gakki!",image)                #显示图像
    # cv2.waitKey(0)

    cv2.imwrite('face.jpg', image)

    return faces