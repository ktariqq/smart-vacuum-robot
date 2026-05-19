# Import necessary libraries
from gpiozero import Motor, PWMOutputDevice, DistanceSensor  # For motors, vacuum motor, and ultrasonic sensors
from time import sleep, time  # For delays and timing
from picamera2 import Picamera2  # To access the Raspberry Pi Camera Module

# Initialize the PiCamera2 module and start the camera preview
camera = Picamera2()
camera.start_preview()

# --- SENSOR SETUP (HC-SR04 ULTRASONIC) ---
# Front sensor connected to trigger pin GPIO4 and echo pin GPIO17
front_sensor = DistanceSensor(echo=17, trigger=4)
# Left sensor connected to trigger pin GPIO22 and echo pin GPIO27
left_sensor = DistanceSensor(echo=27, trigger=22)

# --- MOTOR SETUP ---
# Left DC motor connected to GPIO14 (forward) and GPIO15 (backward)
left_motor = Motor(forward=14, backward=15)
# Right DC motor connected to GPIO18 (forward) and GPIO23 (backward)
right_motor = Motor(forward=18, backward=23)
# Vacuum motor (PWM-controlled) connected to GPIO24
vacuum_motor = PWMOutputDevice(24)

# --- STATE MACHINE INITIAL STATE ---
# Start in "Output Event" (OE) idle state
current = "OE_idle"
state_start_time = time()

# --- OBSTACLE DETECTION THRESHOLD ---
# Set to 0.25 meters (25 cm). If obstacle is closer than this, robot should avoid it
obstacle_threshold = 0.25

# --- STATE TRANSITION FUNCTIONS ---

# Transition from any OS state to start cleaning
def move_to_cleaning():
    global current, state_start_time
    current = "OE_cleaning"
    state_start_time = time()

# Transition from any OS state to idle state
def move_to_idle():
    global current, state_start_time
    current = "OE_idle"
    state_start_time = time()

# --- OBSTACLE CHECKING FUNCTION ---
# Returns True if an obstacle is detected by either sensor
def check_obstacles():
    return front_sensor.distance < obstacle_threshold or left_sensor.distance < obstacle_threshold

# --- OBSTACLE AVOIDANCE ROUTINE ---
# Moves the robot back briefly and turns it to avoid obstacles
def avoid_obstacle():
    # Move both motors backward for 0.5 seconds
    left_motor.backward()
    right_motor.backward()
    sleep(0.4)

    # Spin in place to the right (left motor forward, right motor backward) for 0.5 seconds
    left_motor.forward()
    right_motor.backward()
    sleep(0.5)

# --- MAIN LOOP / STATE MACHINE ---
def main():
    global current, state_start_time

    while True:

        # --- OE_IDLE TRANSITION ---
        if current == "OE_idle":
            vacuum_motor.value = 0  # Turn off vacuum
            left_motor.stop()       # Stop movement
            right_motor.stop()
            current = "OS_idle"     # Move to "Observed State" idle
            print("State: IDLE")

        # --- OS_IDLE STATE ---
        elif current == "OS_idle":
            camera.capture_file("idle.jpg")  # Take a snapshot of the environment

            # After 5 seconds, transition to cleaning
            if time() - state_start_time > 5:
                move_to_cleaning()

        # --- OE_CLEANING TRANSITION ---
        elif current == "OE_cleaning":
            vacuum_motor.value = 1  # Turn vacuum motor on at full speed
            left_motor.forward()    # Start moving forward
            right_motor.forward()
            current = "OS_cleaning"  # Move to cleaning state
            print("State: CLEANING")

        # --- OS_CLEANING STATE ---
        elif current == "OS_cleaning":

            if check_obstacles():  # If an obstacle is detected
                print("Obstacle detected!")
                avoid_obstacle()   # Avoid it

            else:
                # Otherwise, keep moving forward
                left_motor.forward()
                right_motor.forward()

            # After 30 seconds of cleaning, return to idle
            if time() - state_start_time > 30:
                move_to_idle()

        sleep(0.1)  # Loop delay to avoid CPU overload

# --- PROGRAM START ---
# Start the state machine if this file is run directly
if __name__ == "__main__":
    main()
