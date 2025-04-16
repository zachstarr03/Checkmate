import math
import serial
import time

# === Serial Setup ===
# arduino = serial.Serial('COM11', 9600)  # Update port if needed
# time.sleep(2)  # Let Arduino boot

# Lengths (in inches)
L1 = 7.5  # Shoulder to elbow
L2 = 8.75  # Elbow to wrist
L3 = 5.75   # Wrist to claw

# wrist to the end of the gripper is 9 inches

# Arm base position
base_x = 6.65
base_y = -4.5
base_z = 4

# Chess tile position (center of A8)
tile_x = 0.805
tile_y = 12.075

tile_z = 0  # On board surface

# Target offset
target_x = tile_x - base_x
target_y = tile_y - base_y
target_z = tile_z - base_z

# Horizontal and 3D distances
r_xy = math.hypot(target_x, target_y)
r = math.sqrt(r_xy**2 + target_z**2)

# 1. Base angle (rotates from A to H: A8 = 45°, H8 = 135°)
theta_base = math.degrees(math.atan2(target_y, target_x))
theta_base = theta_base  # Center (D/E) is 90°

# 2. Elbow angle using cosine law
cos_theta_elbow = (r**2 - L1**2 - L2**2) / (2 * L1 * L2)
cos_theta_elbow = max(min(cos_theta_elbow, 1), -1)  # Clamp for safety
theta_elbow = math.degrees(math.acos(cos_theta_elbow))

# 3. Shoulder angle
phi = math.atan2(target_z, r_xy)
acos_arg = (L1**2 + r**2 - L2**2) / (2 * L1 * r)
acos_arg = max(min(acos_arg, 1), -1)  # Clamp to prevent math domain error
psi = math.acos(acos_arg)
theta_shoulder = math.degrees(phi + psi)

# 4. Wrist angle (to keep claw level)
theta_wrist = 180 - theta_elbow - theta_shoulder

# Adjust angles to match servo orientation
servo_base = round(theta_base) - 5
servo_left_shoulder = round(155 - theta_shoulder)
servo_right_shoulder = round(theta_shoulder + 10) # Counter motor
servo_elbow = round(theta_elbow)
servo_wrist = round(theta_wrist)

# Show calculated angles
print("Base:", servo_base)
print("Left Shoulder:", servo_left_shoulder)
print("Right Shoulder:", servo_right_shoulder)
print("Elbow:", servo_elbow)
print("Wrist:", servo_wrist)

# === Send to Arduino ===
#arduino = serial.Serial('/dev/ttyACM0', 9600)  # Update with correct port
#time.sleep(2)  # Wait for Arduino to boot

# Format: base left right elbow wrist
#command = f"{servo_base} {servo_left_shoulder} {servo_right_shoulder} {servo_elbow} {servo_wrist}\n"
#arduino.write(command.encode())
#print("Sent:", command)
