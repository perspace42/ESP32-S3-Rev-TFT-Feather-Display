'''
Author: Scott Field
Name: Adafruit Sensor Output Program
Version: 2.0
Purpose:
Using the adafruit_sht4x sensor attached to the ESP32-S3 Rev TFT Feather Board output:
-   Temperature (In Farenheit)
-   Humidity
-   EMC (Left Justified) , Battery Life (Right Justified)

Using the three buttons create the following functions
-   Mode 1: Remain On Continuously / Enter Sleep Mode (Switches)
-   Mode 2: Turn on for 1 Minute Then Go To Sleep
-   Mode 3: Display Users Name and Company Logo To Screen
'''

#Libraries (CircuitPython) 
import time
import board
import displayio # type: ignore
#Temperature Sensor Library
import adafruit_sht4x
#Battery Life Library
import adafruit_max1704x
#GUI Library
#import terminalio
from adafruit_display_text import label
from adafruit_bitmap_font import bitmap_font
#import adafruit_st7789
import digitalio
#import alarm
import alarm




# Function To Find EMC
def getEMC(temperature, humidity):
    RH = .01 * humidity
    W = 330 + (.452 * temperature) + (.00415 * temperature * temperature)
    K = .791 + (.000463 * temperature) - (.000000844 * temperature * temperature)
    K1 = 6.34 + (.000775 * temperature) - (.0000935 * temperature * temperature)
    K2 = 1.09 + (.0284 * temperature) - (.0000904 * temperature * temperature)
    Term1 = ((K * RH) / (1 - (K * RH)))
    Term2 = (K1 * K * RH) + (2 * K1 * K2 * K * K * RH * RH)
    Term3 = 1 + (K1 * K * RH) + (K1 * K2 * K * K * RH * RH)
    EMC = (1800 / W) * ((Term1) + (Term2 / Term3))
    return EMC

# Function To Convert To Farenheit
def toFarenheit(temperature):
    return temperature * 1.8 + 32

# Function To Update Text
def updateText(temperature, humidity, emc, battery):
    temp_label.text = f"Temp: {toFarenheit(temperature):.1f} F"
    humidity_label.text = f"Hum: {humidity:.1f}%"
    emc_label.text = f"EMC: {emc:.1f}"
    battery_label.text = f"Bat: {battery:.1f}%"

# Connect To Board

# Create Inter-Integrated Circuit
i2c = board.I2C()   # uses board.SCL and board.SDA

# Create Instance To Interact With SHT4x Sensor using Inter-Integrated Circuit 
sht = adafruit_sht4x.SHT4x(i2c)

# Create Instance To Calculate Battery Using Onboard Sensor
max1704x = adafruit_max1704x.MAX17048(i2c)

# Disable Sensors Heater, Using The Highest Precision For Temperature and Humidity Measurements
sht.mode = adafruit_sht4x.Mode.NOHEAT_HIGHPRECISION

# Create a Group
group = displayio.Group()
board.DISPLAY.root_group = group

# Setup Font
loadedFont = bitmap_font.load_font("/fonts/Arial24-33.bdf")

# Setup Labels
# Temperature
temp_label = label.Label(font=loadedFont, text=f"Temperature: ", color=0xFFFFFF)
temp_label.x = 10
temp_label.y = 10

# Humidity
humidity_label = label.Label(font=loadedFont, text=f"Humidity: ", color=0xFFFFFF)
humidity_label.x = 10
humidity_label.y = 45

# EMC
emc_label = label.Label(font=loadedFont, text=f"EMC: ", color=0xFFFFFF)
emc_label.x = 10
emc_label.y = 80

# Battery 
battery_label = label.Label(font=loadedFont, text=f"Battery: ", color=0xFFFFFF)
battery_label.x = 60
battery_label.y = 115


# Add labels to the group
group.append(temp_label)
group.append(humidity_label)
group.append(emc_label)
group.append(battery_label)

# Define Buttons
'''
btnD0 = digitalio.DigitalInOut(board.D0)
btnD0.direction = digitalio.Direction.INPUT
btnD0.pull = digitalio.Pull.DOWN
'''

btnD1 = digitalio.DigitalInOut(board.D1)
btnD1.direction = digitalio.Direction.INPUT
btnD1.pull = digitalio.Pull.DOWN

btnD2 = digitalio.DigitalInOut(board.D2)
btnD2.direction = digitalio.Direction.INPUT
btnD2.pull = digitalio.Pull.DOWN

# Main Loop
def main():
    # Retrieve Temperature and Humidity
    temperature, humidity = sht.measurements

    # Calculate EMC
    emc = getEMC(temperature, humidity)
    battery = min(100.0, max1704x.cell_percent)

    # Update the labels with sensor data
    updateText(temperature, humidity, emc, battery)

    # Refresh the display
    board.DISPLAY.refresh()

    # Wait 1 Second Before Calculating Values Again
    time.sleep(1)


# Flag Variables
sleepMode = False

# Main Program Loop
while True:

    #Check For Button Presses
    #Enter Deep Sleep Mode Until Button Pressed Again
    if btnD1.value:
        #Define Alarm
        sleepAlarm = alarm.pin.PinAlarm(pin=board.D0, value=False, pull=True)
        alarm.exit_and_deep_sleep_until_alarms(sleepAlarm)

    #Enter Light Sleep Mode For 60 Seconds Then Turn On for 5 Seconds Continously
    if btnD2.value:
        sleepMode = not sleepMode
        while sleepMode:
            #Sleep for 60 seconds
            board.DISPLAY.brightness = 0
            sleepAlarm = alarm.time.TimeAlarm(monotonic_time=time.monotonic() + 15)
            alarm.light_sleep_until_alarms(sleepAlarm)
            

            #Turn on board
            board.DISPLAY.brightness = 1.0

            stop = time.monotonic() + 10

            while (time.monotonic() <= stop):
                main()

                #If button pressed again
                if btnD2.value:
                    sleepMode = False
                    time.sleep(2)
                    break
                
                #If sleep button pushed once
                if btnD1.value:
                    #Define Alarm
                    sleepAlarm = alarm.pin.PinAlarm(pin=board.D0, value=False, pull=True)
                    alarm.exit_and_deep_sleep_until_alarms(sleepAlarm)
            
            
    #Call main if no buttons pressed        
    main()