import sys
import os
import cv2
import numpy as np
from pyzbar.pyzbar import decode

scancode = ""            #resulting barcode text also used as filename
image = sys.argv[1]      #get image from command line
cixfile = ""

BEGIN_CODE = 'BEGIN'
END_CODE = 'END'
MAINDATA = 'MAINDATA'
MACRO = 'MACRO'          #variables to be used in parsing the file
DRILL_ID = 'BV'
DIA = 'DIA'
DRILL_DIA = 8.0


#get text from barcode

def BarcodeReader(image):

    img = cv2.imdecode(np.fromfile(image, dtype=np.uint8), cv2.IMREAD_UNCHANGED)
    detectedBarcodes = decode(img)

    if not detectedBarcodes:
        print("Barcode Not Detected or your barcode is blank/corrupted!")
    else:
        for barcode in detectedBarcodes:
            (x, y, w, h) = barcode.rect

            cv2.rectangle(img, (x-10, y-10),
                        (x + w+10, y + h+10),
                        (255, 0, 0), 2)
            
            if barcode.data!=b"":
                global scancode
                scancode = barcode.data.decode()+'.CIX'


def find_file(output):
    
    directory = 'c:/Users/punge/OneDrive/Desktop/Work Related/Project final/'   #change this to the directory with the .cix files

    for filename in os.listdir(directory):
        if output == scancode:
            print(f"File found: {scancode}")
            global cixfile
            cixfile = scancode
            return filename
    # If no file is found
    print("File not found")

def parseSection(cixfile):
    key = ''
    content = ''
    results = []
    with open (cixfile, 'r') as file:
        for line in (line.lstrip().rstrip() for line in file):
            if (line.startswith(BEGIN_CODE)):
                key = line[6:]
                content = []
            elif (line.startswith(END_CODE)):
                results.append([key, content])
            else:
                content.append(line)
    return results
        
def parseMaindata(maindata):
    for section in maindata:
        if (section[0] == MAINDATA):
            x = 0
            y = 0
            z = 0
            for lineSplit in (line.split("=") for line in section[1]):
                if (lineSplit[0] == 'LPX'):
                    x = lineSplit[1]
                if (lineSplit[0] == 'LPY'):
                    y = lineSplit[1]
                if (lineSplit[0] == 'LPZ'):
                    z = lineSplit[1]
                    URZdown = str(float(z) / 1000)
                    URZup = str(float(z) / 1000 + 0.1)
            return [x, y, z, URZdown, URZup]
        
def parseDrill(drillData):
    result = []
    for section in drillData:
        if (section[0] == MACRO):
            if (section[1][0].split("=")[1] == DRILL_ID):
                found = False
                drill_x = 0
                drill_y = 0
                for line in (line.split(',') for line in section[1][1:]):
                    if (len(line) == 3 and line[1].split('=')[1] == 'X'):
                        drill_x = float(line[2].split('=')[1])
                    if (len(line) == 3 and line[1].split('=')[1] == 'Y'):
                        drill_y = float(line[2].split('=')[1])
                    if (len(line) == 3 and line[1].split('=')[1] == DIA and float(line[2].split('=')[1]) == DRILL_DIA):
                        found = True
                if (found):
                    result.append([drill_x, drill_y])
    return result

BarcodeReader(image)
find_file(scancode)
sections = parseSection(cixfile)
maindata = parseMaindata(sections)


ori = cixfile.replace('.CIX', '')  #removes .CIX from filename

with open(str(ori)+'.script', 'w') as f:
    f.write('def initialize():\n')
    f.write('   global speed_ms = 0.3\n')
    f.write('   global speed_rads = 0.75\n')       
    f.write('   global accel_mss = 3\n')
    f.write('   global accel_radss = 1.2\n')
    f.write('   global blend_radius = 0.001\n')
    f.write('   set_tcp(p[0.000000, -0.077000, 0.150000, 0.000000, 0.000000, 0.000000])\n\n')

    f.write('def home():\n')
    f.write('   movej([2.126728, -1.207225, -4.744419, 1.239255, 1.570796, 0.555932],accel_radss,speed_rads,0,blend_radius_m)\n\n')

    f.write('def '+str(ori)+'():\n')
    f.write('   set_reference(p[0.612228, -0.525825, 0.000000, 0.000000, 0.000000, 0.000000]\n')
    f.write('   ref_frame = p[0.612228, -0.525825, 0.000000, 0.000000, 0.000000, 0.000000]\n')

    for i in parseDrill(sections):
        f.write('   movel(pose_trans(ref_frame,p['+str(i[0]/1000)+', '+str(i[1]/1000)+', '+(maindata)[4]+', 3.1459265, 0.000000, 0.000000])\n')
        f.write('   movel(pose_trans(ref_frame,p['+str(i[0]/1000)+', '+str(i[1]/1000)+', '+(maindata)[3]+', 3.1459265, 0.000000, 0.000000])\n')
        f.write('   StartGlue()'+'\n')
        f.write('   sleep(0.5000)'+ '\n')
        f.write('   StopGlue()'+'\n')
        f.write('   movel(pose_trans(ref_frame,p['+str(i[0]/1000)+', '+str(i[1]/1000)+', '+(maindata)[4]+', 3.1459265, 0.000000, 0.000000])\n')

    f.write('end') 

print(maindata)
print (parseDrill(sections),'\n')
print (maindata[3])



