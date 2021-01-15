import RPi.GPIO as GPIO
import face_recognition
import picamera
import numpy as np
import os
import time
import lcddriver
import datetime
import pymysql
import atexit
import subprocess



from gpiozero import CPUTemperature

cpu = CPUTemperature()


display = lcddriver.lcd()
display.lcd_clear()
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
time.sleep(1)
output = np.empty((240, 320, 3), dtype=np.uint8)


# Open database connection
db = pymysql.connect("10.44.2.159","remote","1111","TorresTech" )
db.autocommit(True)

def exit_handler():
    display.lcd_display_string((" SHUTTING  DOWN "), 1)
    display.lcd_display_string(("    GOOD BYE    "), 2)

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

countero = 0
while True:
    time.sleep(1)
    dist = distance()

    if dist < 80:
        print("Scanning Face.")
        display.lcd_display_string(("    SCANNING    "), 1)
        display.lcd_display_string(("      FACE      "), 2)

        camera.capture(output, format="rgb")

        face_locations = face_recognition.face_locations(output)

        print("Capturing image.")
        display.lcd_display_string(("CAPTURING IMAGE."), 1)
        display.lcd_display_string(("****************"), 2)

        #camera.capture(output, format="rgb")

        #face_locations = face_recognition.face_locations(output)
        print("Found {} faces in Camera.".format(len(face_locations)))
        face_encodings = face_recognition.face_encodings(output, face_locations)

        if len(face_locations) < 1:
            display.lcd_display_string(("NO FACE DETECTED"), 1)
            display.lcd_display_string(("----------------"), 2)
            time.sleep(0.5)

        if len(face_locations) > 1:
            display.lcd_display_string((" MULTIPLE FACES "), 1)
            display.lcd_display_string(("    DETECTED    "), 2)
            time.sleep(0.5)

        if cpu.temperature > 80:
            print("Your Machine is too HOT")
            print("Shutdown in 5 seconds...")
            time.sleep(5)
            display.lcd_display_string(("  DEVICE ERROR  "), 1)
            display.lcd_display_string(("PLEASE UNPLUG ME"), 2)
            os.system('sudo shutdown -h now')

        for face_encoding in face_encodings:
            match = face_recognition.compare_faces(known_face_encoding, face_encoding, tolerance = 0.45)
            matches=np.where(match)[0] #Checking which image is matched
            print(str(len(matches)) + " MATCH")
            match_count = len(matches)
            if match_count == 1:
                name = str(known_person[matches[0]])
                print(" varirable name = " + name)
                display.lcd_clear()
                try:
                    now = datetime.datetime.now()
                    nowHour = int(now.strftime("%H"))
                    month = now.strftime("%B").lower()
                    day_number = now.strftime("%d").lstrip("0")
                    today7o1am = now.replace(hour=7, minute=1, second=0, microsecond=0)
                    today11o1am = now.replace(hour=11, minute=1, second=0, microsecond=0)
                    today7o1pm = now.replace(hour=19, minute=1, second=0, microsecond=0)
                    today11o1pm = now.replace(hour=23, minute=1, second=0, microsecond=0)
                    today12o1am = now.replace(hour=00, minute=1, second=0, microsecond=0)
                    cursor = db.cursor()
                    cursor.execute(f"SELECT firstname, middlename, lastname, company, shift, face_id, id FROM contractor_employee WHERE id_number = {name}")
                    results = cursor.fetchall()
                    for row in results:
                        fname = row[0]
                        mname = row[1]
                        lname = row[2]
                        company = row[3]
                        shift = row[4]
                        face_id = row[5]
                        id = row[6]
                    cursor.close()
                    if not results:
                        transaction = " FACE MATCHED!. "
                        nome = "BUT UNREGISTERED"
                    else:
                        if shift == "DS" and now < today11o1am:
                        #DAY SHIFT
                            #LOGIN
                            cursor = db.cursor()
                            cursor.execute(f"SELECT * FROM contractor_logbox WHERE face_id = {face_id} AND transaction = 'I' AND DATE(date_time) = '{datetime.date.today()}'")
                            data_login = cursor.fetchall()
                            if not data_login:
                            #INSERT LOGIN
                                cursor.execute(f"INSERT INTO contractor_logbox (date_time, transaction, face_id, shift) VALUES('{datetime.datetime.now()}', 'I', {face_id}, '{shift}')")
                                #db.commit()
                                if now < today7o1am:
                                    status = 'P'
                                else:
                                    status = 'L'
                                cursor.execute(f"UPDATE contractor_employee SET status='{status}' WHERE id = {id}")
                                #db.commit()
                                cursor.execute(f"UPDATE contractor_{month} SET d{day_number} = '{status}' WHERE id = {id}")
                                #db.commit()
                                transaction = "     LOGIN      "
                                nome = f"{fname[0]}.{mname[0]}. {lname}"
                            else:
                                #REPEATED LOGIN
                                transaction = " REPEATED LOGIN "
                                nome = f"{fname[0]}.{mname[0]}. {lname}"
                            cursor.close()
                            data_login *= 0
                        elif shift=="DS" and now >= today11o1am :
                        #DAY SHIFT
                            #LOGOUT
                            cursor = db.cursor()
                            cursor.execute(f"SELECT * FROM contractor_logbox WHERE face_id = {face_id} AND transaction = 'O' AND DATE(date_time) = '{datetime.date.today()}'")
                            data_logout = cursor.fetchall()
                            if not data_logout:
                                #INSERT LOGOUT

                                #IF Out is 3:30 to 4:00 out = 4:00=========================================================================================================
                                now = datetime.datetime.now()
                                noon = datetime.datetime.now().replace(hour=15, minute=30, second=0, microsecond=0)
                                noona = datetime.datetime.now().replace(hour=16, minute=0, second=59, microsecond=999999)
                                if noon <= now and now <= noona:
                                    now = now.replace(hour=16, minute=0, second=0, microsecond=0)
                                cursor.execute(f"INSERT INTO contractor_logbox (date_time, transaction, face_id, shift) VALUES ('{now}', 'O', {face_id}, '{shift}')")
                                #==========================================================================================================================================

                                #uncomment if  3:30 to 4:00 is removed
                                #cursor.execute(f"INSERT INTO contractor_logbox (date_time, transaction, face_id, shift) VALUES ('{datetime.datetime.now()}', 'O', {face_id}, '{shift}')")
                                #db.commit()
                                transaction = "     LOGOUT     "
                                nome = f"{fname[0]}.{mname[0]}. {lname}"
                            else:
                                #REPEATED LOGOUT
                                transaction = "REPEATED  LOGOUT"
                                nome = f"{fname[0]}.{mname[0]}. {lname}"
                            cursor.close()
                            data_logout *= 0
                        elif shift=="NS" and now < today11o1pm and now > today11o1am:
                        #NIGH SHIFT
                            #LOGIN
                            cursor = db.cursor()
                            cursor.execute(f"SELECT * FROM contractor_logbox WHERE face_id = {face_id} AND transaction = 'I' AND DATE(date_time) = '{datetime.date.today()}'")
                            data_loginNS = cursor.fetchall()
                            if not data_loginNS:
                                #INSERT LOGIN
                                cursor.execute(f"INSERT INTO contractor_logbox (date_time, transaction, face_id, shift) VALUES ('{datetime.datetime.now()}','I', {face_id}, '{shift}')")
                                #db.commit()
                                if now < today7o1pm:
                                    status = 'P'
                                else:
                                    status = 'L'
                                cursor.execute(f"UPDATE contractor_employee SET status='{status}' WHERE id = {id}")
                                #db.commit()
                                cursor.execute(f"UPDATE contractor_{month} SET d{day_number} = '{status}' WHERE id = {id}")
                                #db.commit()
                                transaction = "     LOGIN      "
                                nome = f"{fname[0]}.{mname[0]}. {lname}"
                            else:
                                #REPEATED LOGIN
                                transaction = " REPEATED LOGIN "
                                nome = f"{fname[0]}.{mname[0]}. {lname}"
                            cursor.close()
                            data_loginNS *= 0
                        elif shift=="NS" and now < today7o1am and now > today12o1am:
                        #NIGHT SHIFT
                            #LOGOUT
                            cursor = db.cursor()
                            cursor.execute(f"SELECT * FROM contractor_logbox WHERE face_id = {face_id} AND transaction = 'O' AND DATE(date_time) = '{datetime.date.today()}'")
                            data_logoutNS = cursor.fetchall()
                            if not data_logoutNS:
                                #INSERT LOGOUT
                                cursor.execute(f"INSERT INTO contractor_logbox (date_time, transaction, face_id, shift) VALUES ('{datetime.datetime.now()}', 'O', {face_id}, '{shift}')")
                                #db.commit()
                                transaction = "     LOGOUT     "
                                nome = f"{fname[0]}.{mname[0]}. {lname}"
                            else:
                                #REPEATED LOGOUT
                                transaction = "REPEATED  LOGOUT"
                                nome = f"{fname[0]}.{mname[0]}. {lname}"
                            cursor.close()
                            data_logoutNS *= 0
                        else:
                            transaction = "     ERROR!     "
                            nome = "  PLS  REPORT  "
                    results *= 0
                except Exception as ex:
                    print(ex)
                    transaction = "FACEMATCHED WITH"
                    nome        = "ERROR PLS REPORT"
            else:
                name = "NO FILENAME FOUND"
                print("NO FACE MATCH")
                #time.sleep(1)
                #subprocess.call("logbox.sh")

                #transaction = "   NO RECORD!   "
                #nome = " IMAGE RECORDED "
                camera.close()
                os.system("/home/pi/Desktop/TEST/logbox.sh")

                camera = picamera.PiCamera()
                camera.resolution = (320, 240)
                camera.framerate = 5
                time.sleep(1)
                output = np.empty((240, 320, 3), dtype=np.uint8)

                #transaction = "     ERROR!     "
                #nome = "   NO RECORD!   "
                transaction = "   NO RECORD!   "
                nome = " IMAGE RECORDED "

                display.lcd_clear()
            print(name)
            display.lcd_display_string((transaction), 1)
            display.lcd_display_string(nome, 2)
            print(transaction)
            print(nome)
            name = ""
            time.sleep(2)
    else:
        if countero >= 30:
            print(" ")
            print("Waiting Face")
            print("Distance =" , dist , "       CPU Temp =" , cpu.temperature)
            countero = 0

        countero += 1

        display.lcd_display_string(str(datetime.datetime.now().strftime("%b %d, %Y %A") ), 1)
        display.lcd_display_string(str(datetime.datetime.now().strftime("  " + "%I:%M:%S " + " " + "%p ") ) , 2)

        if cpu.temperature > 70:
            print("Your Machine is too HOT")
            print("Shutdown in 5 seconds...")
            time.sleep(5)
            display.lcd_display_string(("  DEVICE ERROR  "), 1)
            display.lcd_display_string(("PLEASE UNPLUG ME"), 2)
            os.system('sudo shutdown -h now')

#        atexit.register(exit_handler)
