import RPi.GPIO as GPIO
import face_recognition
import picamera
import numpy as np
import os
import time
import lcddriver
import datetime

from gpiozero import CPUTemperature

cpu = CPUTemperature()


display = lcddriver.lcd()

GPIO.setmode(GPIO.BCM)
GPIO.setwarnings(False) 




GPIO_TRIGGER = 18
GPIO_ECHO = 24

GPIO.setup(GPIO_TRIGGER, GPIO.OUT)
GPIO.setup(GPIO_ECHO, GPIO.IN)


print("Loading known face image(s)")


face_locations = []
face_encodings = []
face_names = []

known_person=[]
known_image=[]
known_face_encoding=[]


display.lcd_clear()
display.lcd_display_string(("FACE RECOGNITION") , 1)
display.lcd_display_string(("  PLEASE WAIT!  ") , 2)


camera = picamera.PiCamera()
camera.resolution = (320, 240)
camera.framerate = 5

#camera.brightness = 60
#camera.contrast = 35
#camera.saturation = 30

time.sleep(1)
output = np.empty((240,320, 3), dtype=np.uint8)




def distance():
    # set Trigger to HIGH
    GPIO.output(GPIO_TRIGGER, True)

    # set Trigger after 0.01ms to LOW
    time.sleep(0.00001)
    GPIO.output(GPIO_TRIGGER, False)

    StartTime = time.time()
    StopTime = time.time()

    # save StartTime
    while GPIO.input(GPIO_ECHO) == 0:
        StartTime = time.time()

    # save time of arrival
    while GPIO.input(GPIO_ECHO) == 1:
        StopTime = time.time()

    # time difference between start and arrival
    TimeElapsed = StopTime - StartTime
    # multiply with the sonic speed (34300 cm/s)
    # and divide by 2, because there and back
    distance = (TimeElapsed * 34300) / 2

    return distance



for file in os.listdir("IMAGE"):
    try:
        known_person.append(file.replace(".jpg", ""))
        file=os.path.join("IMAGE/", file)
        known_image = face_recognition.load_image_file(file)
        known_face_encoding.append(face_recognition.face_encodings(known_image)[0])
    except Exception as e:
        pass


display.lcd_clear()


while True:
    time.sleep(1)
    dist = distance()

    if dist < 70:

      print("Capturing image.")
      display.lcd_display_string(("CAPTURING IMAGE."), 1)
      display.lcd_display_string(("****************"), 2)

      camera.capture(output, format="rgb")

      face_locations = face_recognition.face_locations(output)
      print("Found {} faces in image.".format(len(face_locations)))
      face_encodings = face_recognition.face_encodings(output, face_locations)


      if cpu.temperature > 70:
          print("Your Machine is too HOT")
          print("Shutdown in 5 seconds...")
          time.sleep(5)
          display.lcd_display_string(("  DEVICE ERROR  "), 1)
          display.lcd_display_string(("PLEASE UNPLUG ME"), 2)
          os.system('sudo shutdown -h now')



      for face_encoding in face_encodings:

          match = face_recognition.compare_faces(known_face_encoding, face_encoding, tolerance = 0.44)
          matches=np.where(match)[0] #Checking which image is matched
          if len(matches)>0:
            name = str(known_person[matches[0]])
            display.lcd_clear()

          else:
            name = "NO RECORD FOUND "
            display.lcd_clear()

          print(name)
          display.lcd_display_string(("     LOG-IN    "), 1)
          display.lcd_display_string(name, 2)
          time.sleep(2)


    else:

      print(" ")

      print("Waiting Face")

      print("Distance =" , dist , "       CPU Temp =" , cpu.temperature)

      display.lcd_display_string(str(datetime.datetime.now().strftime("%b %d, %Y %A") ), 1)
      display.lcd_display_string(str(datetime.datetime.now().strftime("  " + "%I:%M:%S " + " " + "%p ") ) , 2)

      if cpu.temperature > 70:

          print("Your Machine is too HOT")
          print("Shutdown in 5 seconds...")
          time.sleep(5)
          display.lcd_display_string(("  DEVICE ERROR  "), 1)
          display.lcd_display_string(("PLEASE UNPLUG ME"), 2)
          os.system('sudo shutdown -h now')

