import cv2
import numpy as np
import os

img = np.ones((1000, 1600, 3), dtype=np.uint8) * 255

# Border
cv2.rectangle(img, (40, 40), (1560, 960), (0, 0, 0), 3)
cv2.putText(img, 'CRUDE DISTILLATION UNIT 2 - P&ID SYSTEM B', (60, 80), cv2.FONT_HERSHEY_SIMPLEX, 1.0, (0, 0, 0), 2)

# Equipment: Tank TK-201
cv2.rectangle(img, (150, 350), (320, 750), (0, 0, 0), 3)
cv2.ellipse(img, (235, 350), (85, 30), 0, 180, 360, (0, 0, 0), 3)
cv2.ellipse(img, (235, 750), (85, 30), 0, 0, 180, (0, 0, 0), 3)
cv2.putText(img, 'TK-201', (185, 540), cv2.FONT_HERSHEY_SIMPLEX, 0.9, (0, 0, 0), 2)
cv2.putText(img, 'FEED STORAGE TANK', (160, 580), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 0), 1)

# Suction process line from TK-201 to Pump P-201
cv2.line(img, (320, 600), (600, 600), (0, 0, 0), 4)
cv2.putText(img, 'PL-201', (420, 585), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 0), 2)

# Pump P-201
cv2.circle(img, (650, 600), 50, (0, 0, 0), 3)
cv2.line(img, (650, 550), (650, 400), (0, 0, 0), 4) # Discharge nozzle
cv2.putText(img, 'P-201', (615, 610), cv2.FONT_HERSHEY_SIMPLEX, 0.9, (0, 0, 0), 2)

# Discharge line from P-201 to Exchanger E-205
cv2.line(img, (650, 400), (1050, 400), (0, 0, 0), 4)
cv2.putText(img, 'PL-202', (750, 385), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 0), 2)

# Valve CV-201 on discharge line
cv2.line(img, (820, 380), (860, 420), (0, 0, 0), 2)
cv2.line(img, (860, 380), (820, 420), (0, 0, 0), 2)
cv2.line(img, (820, 380), (820, 420), (0, 0, 0), 2)
cv2.line(img, (860, 380), (860, 420), (0, 0, 0), 2)
cv2.putText(img, 'CV-201', (810, 450), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 0), 2)

# Exchanger E-205
cv2.rectangle(img, (1050, 320), (1350, 480), (0, 0, 0), 3)
cv2.putText(img, 'E-205', (1160, 390), cv2.FONT_HERSHEY_SIMPLEX, 0.9, (0, 0, 0), 2)
cv2.putText(img, 'PREHEAT EXCHANGER', (1100, 430), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 0), 1)

# Instrument loop: TT-205 on Exchanger
cv2.circle(img, (1200, 240), 30, (0, 0, 0), 2)
cv2.putText(img, 'TT-205', (1155, 248), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 0), 2)
# Dashed signal line to E-205
for y in range(270, 320, 10):
    cv2.line(img, (1200, y), (1200, y+5), (0, 0, 0), 2)

# Level Transmitter LT-201 on Tank TK-201
cv2.circle(img, (235, 230), 30, (0, 0, 0), 2)
cv2.putText(img, 'LT-201', (190, 238), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 0), 2)
for y in range(260, 350, 10):
    cv2.line(img, (235, y), (235, y+5), (0, 0, 0), 2)

out_path = 'demo_data/pid/pid_system_b.png'
cv2.imwrite(out_path, img)
print('Generated', out_path, 'size:', os.path.getsize(out_path))
