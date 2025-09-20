import cv2
import os

# Folder where the known faces will be stored
save_path = "static/images/known_faces"

# Create folder if it doesn't exist
os.makedirs(save_path, exist_ok=True)

# Ask for the person's name
name = input("Enter the person's name: ").strip()
filename = os.path.join(save_path, f"{name}.jpg")

# Start webcam
cap = cv2.VideoCapture(0)
print("Press SPACE to take the photo, ESC to cancel.")

while True:
    ret, frame = cap.read()
    cv2.imshow("Capture Face", frame)

    key = cv2.waitKey(1)
    if key % 256 == 27:  # ESC key to cancel
        print("Capture cancelled.")
        break
    elif key % 256 == 32:  # SPACE key to capture
        cv2.imwrite(filename, frame)
        print(f"✅ Saved {filename}")
        break

cap.release()
cv2.destroyAllWindows()
