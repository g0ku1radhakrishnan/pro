import os
import sqlite3
from datetime import datetime
from flask import Flask, render_template, request, redirect, url_for
import cv2
import face_recognition

app = Flask(__name__, static_folder='static')



# ----------------------------
# Initialize Database
# ----------------------------


def init_db():
    conn = sqlite3.connect("attendance.db")
    cursor = conn.cursor()

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS students (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        student_id TEXT,
        name TEXT,
        username TEXT UNIQUE,
        password TEXT,
        department TEXT
    )
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS attendance (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        student_id INTEGER,
        name TEXT,
        class TEXT,
        date TEXT,
        checkin_time TEXT,
        confidence REAL,
        status TEXT
    )
    """)

    cursor.execute("SELECT * FROM students WHERE username=?", ("basil",))
    if cursor.fetchone() is None:
        cursor.execute(
            "INSERT INTO students (student_id, name, username, password, department) VALUES (?, ?, ?, ?, ?)",
            ("S001", "Basil", "basil", "basil123", "MCA-1st year")
        )

    conn.commit()
    conn.close()

init_db()

# ----------------------------
# Attendance Marking
# ----------------------------
def mark_attendance(student_id, name, class_name="Class 10", confidence=99.0, status="Present"):
    conn = sqlite3.connect('attendance.db')
    cursor = conn.cursor()
    now = datetime.now()
    date = now.strftime("%Y-%m-%d")
    time = now.strftime("%H:%M:%S")

    # Always insert a new attendance record
    cursor.execute("""
        INSERT INTO attendance (student_id, name, class, date, checkin_time, confidence, status)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    """, (student_id, name, class_name, date, time, confidence, status))

    conn.commit()
    conn.close()
    print(f"✅ Marked {status} for {name} at {time}")


# ----------------------------
# Routes
# ----------------------------

@app.route('/splash')
def splash():
    return render_template('splash.html')

@app.route('/')
def home():
    return render_template('login.html')

@app.route('/login', methods=['POST'])
def login():
    username = request.form['username']
    password = request.form['password']

    if username == "admin" and password == "admin123":
        return render_template('admin.html')

    conn = sqlite3.connect('attendance.db')
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM students WHERE username=? AND password=?", (username, password))
    student = cursor.fetchone()
    conn.close()

    if student:
        return redirect(url_for('scan'))
    else:
        return "<h1>Invalid Credentials</h1>"

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        try:
            student_id = request.form['student_id']
            name = request.form['name']
            username = request.form['username']
            password = request.form['password']
            department = request.form['department']

            conn = sqlite3.connect('attendance.db')
            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO students (student_id, name, username, password, department) VALUES (?, ?, ?, ?, ?)",
                (student_id, name, username, password, department)
            )
            conn.commit()
            conn.close()

            save_dir = os.path.join("static", "images", "known_faces")
            os.makedirs(save_dir, exist_ok=True)

            cap = cv2.VideoCapture(0)
            instructions = ["Look Straight", "Turn Left", "Turn Right", "Look Up", "Look Down"]
            img_count = 0

            for instruction in instructions:
                captured = False
                while not captured:
                    ret, frame = cap.read()
                    if not ret:
                        continue

                    cv2.putText(frame, instruction, (50, 50), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
                    cv2.imshow("Register Face - Press 'c' to capture", frame)

                    key = cv2.waitKey(1)
                    if key & 0xFF == ord('c'):
                        img_count += 1
                        file_path = os.path.join(save_dir, f"{username}_{img_count}.jpg")
                        cv2.imwrite(file_path, frame)
                        captured = True

                    if key & 0xFF == ord('q'):
                        break

            cap.release()
            cv2.destroyAllWindows()
            return "<h1>✅ Signup Successful! Face Registered</h1>"

        except sqlite3.IntegrityError:
            return "<h1>❌ Username already exists. Try a different one.</h1>"
        except Exception as e:
            return f"<h1>❌ Error: {e}</h1>"

    return render_template('signup.html')

@app.route('/scan')
def scan():
    known_face_encodings = []
    known_face_names = []

    known_faces_dir = os.path.join("static", "images", "known_faces")
    for filename in os.listdir(known_faces_dir):
        if filename.endswith((".jpg", ".png")):
            image_path = os.path.join(known_faces_dir, filename)
            image = face_recognition.load_image_file(image_path)
            encodings = face_recognition.face_encodings(image)
            if encodings:
                known_face_encodings.append(encodings[0])
                known_face_names.append(os.path.splitext(filename)[0])

    attendance_marked_names = []

    video_capture = cv2.VideoCapture(0)
    if not video_capture.isOpened():
        return "<h1>❌ No camera detected</h1>"

    while True:
        ret, frame = video_capture.read()
        if not ret:
            break

        small_frame = cv2.resize(frame, (0, 0), fx=0.25, fy=0.25)
        rgb_small_frame = cv2.cvtColor(small_frame, cv2.COLOR_BGR2RGB)

        face_locations = face_recognition.face_locations(rgb_small_frame)
        face_encodings = face_recognition.face_encodings(rgb_small_frame, face_locations)

        for i, face_encoding in enumerate(face_encodings):
            matches = face_recognition.compare_faces(known_face_encodings, face_encoding)
            name = "Unknown"

            if True in matches:
                first_match_index = matches.index(True)
                name = known_face_names[first_match_index]
                if name not in attendance_marked_names:
                    mark_attendance(student_id=first_match_index + 1, name=name)
                    attendance_marked_names.append(name)

            top, right, bottom, left = face_locations[i]
            top *= 4; right *= 4; bottom *= 4; left *= 4
            cv2.rectangle(frame, (left, top), (right, bottom), (0, 255, 0), 2)
            cv2.putText(frame, f"{name} - Attendance Marked ✅", (left, top - 10),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 0), 2)

        cv2.imshow("Attendance Scan", frame)

        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    video_capture.release()
    cv2.destroyAllWindows()
    return redirect(url_for('scan_complete'))

@app.route('/scan_complete')
def scan_complete():
    return render_template('scan_complete.html')



@app.route('/admin/attendance')
def admin_attendance():
    conn = sqlite3.connect('attendance.db')
    cursor = conn.cursor()
    cursor.execute("""
        SELECT student_id, name, class, date, checkin_time, confidence, status
        FROM attendance
        ORDER BY date DESC, checkin_time DESC
    """)
    records = cursor.fetchall()
    conn.close()
    return render_template('attendance.html', records=records)
    


# ----------------------------
# Run App
# ----------------------------

if __name__ == '__main__':
    app.run(debug=True)
