import os
import cv2
import face_recognition
from app import mark_attendance  # Make sure app.py has mark_attendance function

# Load known faces
known_face_encodings = []
known_face_names = []
faces_dir = os.path.join("static", "images", "known_faces")
for file in os.listdir(faces_dir):
    if file.endswith((".jpg", ".png")):
        image_path = os.path.join(faces_dir, file)
        image = face_recognition.load_image_file(image_path)
        encodings = face_recognition.face_encodings(image)
        if encodings:
            known_face_encodings.append(encodings[0])
            known_face_names.append(os.path.splitext(file)[0])

attendance_marked = []
video_capture = cv2.VideoCapture(0)
process_frame = True

while True:
    ret, frame = video_capture.read()
    if not ret:
        break

    small_frame = cv2.resize(frame, (0, 0), fx=0.25, fy=0.25)
    rgb_small_frame = small_frame[:, :, ::-1]

    if process_frame:
        face_locations = face_recognition.face_locations(rgb_small_frame)
        face_encodings = face_recognition.face_encodings(rgb_small_frame, face_locations)

        for i, face_encoding in enumerate(face_encodings):
            matches = face_recognition.compare_faces(known_face_encodings, face_encoding)
            name = "Unknown"

            if True in matches:
                index = matches.index(True)
                name = known_face_names[index]

                if name not in attendance_marked:
                    mark_attendance(student_id=index+1, name=name)
                    attendance_marked.append(name)

            # Draw rectangle
            top, right, bottom, left = face_locations[i]
            top *= 4
            right *= 4
            bottom *= 4
            left *= 4
            cv2.rectangle(frame, (left, top), (right, bottom), (0, 255, 0), 2)
            cv2.putText(frame, f"{name}", (left, top-10), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 0), 2)

    process_frame = not process_frame
    cv2.imshow("Attendance Scan", frame)

    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

video_capture.release()
cv2.destroyAllWindows()
