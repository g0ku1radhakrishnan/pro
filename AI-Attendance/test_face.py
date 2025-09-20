import face_recognition

# Load a sample picture (replace with path to your test image)
image_path = "test.jpg"  # Put an image file in your AI-Attendance folder
try:
    image = face_recognition.load_image_file(image_path)
except FileNotFoundError:
    print(f"Image not found: {image_path}")
    exit()

# Find all face locations in the image
face_locations = face_recognition.face_locations(image)

if face_locations:
    print(f"✅ Face(s) detected! Total: {len(face_locations)}")
    print("Locations:", face_locations)
else:
    print("❌ No face detected. Try a clearer image.")

# Test encoding extraction
try:
    face_encodings = face_recognition.face_encodings(image)
    if face_encodings:
        print("✅ Face encoding generated successfully!")
    else:
        print("❌ Could not generate encoding.")
except Exception as e:
    print("⚠️ Error generating encoding:", e)
