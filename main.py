import cv2
import mediapipe as mp
import math
from collections import deque, Counter

# Initialize MediaPipe
mp_hands = mp.solutions.hands
mp_draw = mp.solutions.drawing_utils

hands = mp_hands.Hands(
    max_num_hands=1,
    min_detection_confidence=0.6,
    min_tracking_confidence=0.6
)

history = deque(maxlen=5)


# Calculate angle between three landmarks
def calculate_angle(a, b, c):

    ba = (a.x - b.x, a.y - b.y)
    bc = (c.x - b.x, c.y - b.y)

    dot = ba[0] * bc[0] + ba[1] * bc[1]

    mag_ba = math.sqrt(ba[0]**2 + ba[1]**2)
    mag_bc = math.sqrt(bc[0]**2 + bc[1]**2)

    if mag_ba * mag_bc == 0:
        return 0

    cosine = dot / (mag_ba * mag_bc)
    cosine = max(-1, min(1, cosine))

    return math.degrees(math.acos(cosine))


# Recognize gestures
def recognize_gesture(lm):

    # Check finger angles
    index = calculate_angle(lm[5], lm[6], lm[7]) > 155
    middle = calculate_angle(lm[9], lm[10], lm[11]) > 155
    ring = calculate_angle(lm[13], lm[14], lm[15]) > 155
    pinky = calculate_angle(lm[17], lm[18], lm[19]) > 155

    fingers = [index, middle, ring, pinky]

    # Check thumb angle
    thumb_angle = calculate_angle(lm[2], lm[3], lm[4])
    thumb_extended = thumb_angle > 145

    # OPEN HAND
    if all(fingers) and thumb_extended:
        return "OPEN HAND"

    # VICTORY / PEACE
    elif index and middle and not ring and not pinky:
        return "VICTORY / PEACE"

    # THUMBS UP
    elif (
        not any(fingers)
        and thumb_extended
        and lm[4].y < lm[2].y
    ):
        return "THUMBS UP"

    # FIST
    elif not any(fingers) and not thumb_extended:
        return "FIST"

    return "UNKNOWN"


# Start webcam
cap = cv2.VideoCapture(0)

if not cap.isOpened():
    print("Cannot open webcam.")
    hands.close()
    exit()

print("AI Hand Gesture Recognition Started!")
print("Press Q to exit.")

try:

    while True:

        success, frame = cap.read()

        if not success:
            break

        frame = cv2.flip(frame, 1)

        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

        results = hands.process(rgb)

        gesture = "NO HAND DETECTED"

        if results.multi_hand_landmarks:

            for hand_landmarks in results.multi_hand_landmarks:

                mp_draw.draw_landmarks(
                    frame,
                    hand_landmarks,
                    mp_hands.HAND_CONNECTIONS
                )

                current = recognize_gesture(
                    hand_landmarks.landmark
                )

                history.append(current)

                gesture = Counter(history).most_common(1)[0][0]

        else:
            history.clear()

        # Display background
        cv2.rectangle(
            frame,
            (10, 10),
            (470, 90),
            (0, 0, 0),
            -1
        )

        # Display gesture
        cv2.putText(
            frame,
            gesture,
            (25, 60),
            cv2.FONT_HERSHEY_SIMPLEX,
            1,
            (0, 255, 0),
            2
        )

        cv2.imshow(
            "AI Hand Gesture Recognition",
            frame
        )

        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

finally:

    cap.release()
    hands.close()
    cv2.destroyAllWindows()

    print("Camera closed successfully.")