import numpy as np
import cv2
import serial
import time
from time import sleep
ser = serial.Serial('COM4',9600)
import mysql.connector
import datetime
ts = time.time()
timestamp = datetime.datetime.fromtimestamp(ts).strftime('%Y-%m-%d %H:%M:%S')
mydb = mysql.connector.connect (
  host="doctorcare.cpfecuez6wv3.us-east-1.rds.amazonaws.com",
  user="admin",
  password="doctorcare",
  database="system classification"
)
mycursor = mydb.cursor()
cap=img=obj=[]
nObj=0
Px=Py=Or=0.0
Pz=3.0
Col=-1
s=0
h=1
cap = cv2.VideoCapture(0)

cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)

def image():
    global cap, img, Px, Py, Or, Col, Pz
    ret,img = cap.read()
    textX = f'x:{Px}'
    textY = f'y:{Py}'
    textZ = f'z:{Pz}'
    textA = f'a:{Or}'
    if Col==0:
        textC = 'RED'
    elif Col == 2:
        textC = 'YELLOW'
    elif Col == 1:
        textC = 'BLUE'
    elif Col==-1:
        textC = 'NULL'
    cv2.putText(img, textC, (10, 50), cv2.FONT_HERSHEY_COMPLEX, 0.8, (0, 255, 255), 1, cv2.LINE_AA)
    cv2.putText(img, textX, (135, 50), cv2.FONT_HERSHEY_COMPLEX, 0.8, (0, 255, 255), 1, cv2.LINE_AA)
    cv2.putText(img, textY, (260, 50), cv2.FONT_HERSHEY_COMPLEX, 0.8, (0, 255, 255), 1, cv2.LINE_AA)
    cv2.putText(img, textZ, (385, 50), cv2.FONT_HERSHEY_COMPLEX, 0.8, (0, 255, 255), 1, cv2.LINE_AA)
    cv2.putText(img, textA, (510, 50), cv2.FONT_HERSHEY_COMPLEX, 0.8, (0, 255, 255), 1, cv2.LINE_AA)

    cv2.imshow('Objects', img)
    key = cv2.waitKey(1)

def convertCoordinates():
    global obj, Px,Py,Or,Col, h
      
    osX = 17
    osY = 6.8 
                        
    Px = round((obj[1]/28.2 + osX), 2)
    Py = round((obj[0]/28.2 + osY), 2)
    Or = round((obj[2]), 2)
    if Or<-90 : Or+=180
    Col = obj[3]

def ad():
    global s,h,nObj,Px,Py,Pz,Or,Col
    if s: 
        imgProccessing()
        if nObj:
            convertCoordinates()
            s=0
            sendData()
            h=0
        else:
            s=1
            if ~h :
                ser.write(b'h\n')
                h=1;
            sleep(0.1)

def receiveData():
    global s
    if (ser.in_waiting>0):
        Rx = ser.readline()
        Rx = Rx.decode('utf-8', 'ignore')
        Rx = Rx.rstrip()
        if Rx=='4': 
            s=1
            print('Start XLA')
        elif Rx=='5': 
            s=0   
            print('Stop XLA')
        elif Rx=='0':
            sql = "INSERT INTO color (color, date) VALUES (%s, %s)"
            val = ("BLUE", timestamp)
            mycursor.execute(sql, val)
            mydb.commit()
            print(mycursor.rowcount, "record inserted.")
        elif Rx=='1':
            sql = "INSERT INTO color (color, date) VALUES (%s, %s)"
            val = ("GREEN", timestamp)
            mycursor.execute(sql, val)
            mydb.commit()
            print(mycursor.rowcount, "record inserted.")
        elif Rx=='2':
            sql = "INSERT INTO color (color, date) VALUES (%s, %s)"
            val = ("RED", timestamp)
            mycursor.execute(sql, val)
            mydb.commit()
            print(mycursor.rowcount, "record inserted.")
def sendData():
    global Px,Py,Pz,Or,Col
    Tx='obj'+' '+str(Px)+' '+str(Py)+' '+str(Pz)+' '+str(Or)+' '+str(Col)+'\n'
    print(Tx)
    Tx=Tx.encode()
    ser.write(Tx)
    ser.flush()

def  imgProccessing():
    global img,nObj,obj, Px,Py,Pz,Or,Col

    Objects=[]
    kernel = np.ones((5,5),np.uint8)

    hsv_image = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
    
    lower_blue = np.array([100,140,106])
    upper_blue = np.array([120,255,255])
    obj_blue = cv2.inRange(hsv_image, lower_blue, upper_blue)
    obj_blue = cv2.morphologyEx(obj_blue, cv2.MORPH_OPEN,kernel)
    obj_blue = cv2.morphologyEx(obj_blue, cv2.MORPH_CLOSE,kernel)

    lower_green = np.array([25,52,72])
    upper_green = np.array([102,255,255])
    obj_green = cv2.inRange(hsv_image, lower_green, upper_green)
    obj_green = cv2.morphologyEx(obj_green, cv2.MORPH_OPEN,kernel)
    obj_green = cv2.morphologyEx(obj_green, cv2.MORPH_CLOSE,kernel)

    lower_red = np.array([0,50,50])
    upper_red = np.array([10,255,255])
    obj_red = cv2.inRange(hsv_image, lower_red, upper_red)
    obj_red = cv2.morphologyEx(obj_red, cv2.MORPH_OPEN,kernel)
    obj_red = cv2.morphologyEx(obj_red, cv2.MORPH_CLOSE,kernel)

    minarea=18000
    maxarea=20000

    contours, hierarchy = cv2.findContours(obj_red,cv2.RETR_TREE,cv2.CHAIN_APPROX_SIMPLE)
    for c in contours:
        area = cv2.contourArea(c)
        if (area>minarea) & (area<maxarea):
            M = cv2.moments(c)
            cX = int(M["m10"] / M["m00"])
            cY = int(M["m01"] / M["m00"])
            _,_,angle = cv2.fitEllipse(c)
            angle = np.round(angle, decimals=0, out=None)
            if cX <= 400:
                Objects.append ([cX,cY,angle,2])

    
    contours, hierarchy = cv2.findContours(obj_blue,cv2.RETR_TREE,cv2.CHAIN_APPROX_SIMPLE)
    for c in contours:
        area = cv2.contourArea(c)
        if (area>minarea) & (area<maxarea):
            M = cv2.moments(c)
            cX = int(M["m10"] / M["m00"])
            cY = int(M["m01"] / M["m00"])
            _,_,angle = cv2.fitEllipse(c)
            angle = np.round(angle, decimals=0, out=None)
            if cX <= 400:
                Objects.append ([cX,cY,angle,0])


    contours, hierarchy = cv2.findContours(obj_green,cv2.RETR_TREE,cv2.CHAIN_APPROX_SIMPLE)
    for c in contours:
        area = cv2.contourArea(c)
        if (area>minarea) & (area<maxarea):
            M = cv2.moments(c)
            cX = int(M["m10"] / M["m00"])
            cY = int(M["m01"] / M["m00"])
            _,_,angle = cv2.fitEllipse(c)
            angle = np.round(angle, decimals=0, out=None)
            if cX <= 400:
                Objects.append ([cX,cY,angle,1])


    nObj=len(Objects)
    if nObj:
        def X(elem):
            return elem[1]
        Objects.sort(key=X,reverse=True)
        def X(elem):
            return elem[0]
        Objects.sort(key=X,reverse=True)
        obj=Objects[0]
        print(obj)

while (1):
    receiveData()
    image() 
    ad() 
cap.release()
cv2.destroyAllWindows()
ser.close()

