import cv2
import mediapipe as mp

mp_pose = mp.solutions.pose
pose = mp_pose.Pose()
mp_drawing = mp.solutions.drawing_utils

# Load an image
image_path = "person_squat.jpg"  # Put any squat photo here
image = cv2.imread(image_path)

# Convert the image color
image_rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
results = pose.process(image_rgb)

# Draw pose landmarks
if results.pose_landmarks:
    mp_drawing.draw_landmarks(image, results.pose_landmarks, mp_pose.POSE_CONNECTIONS)

# Save and display result
cv2.imwrite("pose_output.jpg", image)
cv2.imshow("Pose Detection", image)
cv2.waitKey(0)
cv2.destroyAllWindows()
