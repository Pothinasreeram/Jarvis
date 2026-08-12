import cv2


def handle_camera_commands(command):

    command = command.lower()

    if "open camera" in command or "camera" in command:

        cap = cv2.VideoCapture(0)

        if not cap.isOpened():
            return "Unable to access the camera."

        while True:
            ret, frame = cap.read()

            if not ret:
                break

            cv2.imshow("JARVIS Camera", frame)

            # Press Q to close
            if cv2.waitKey(1) & 0xFF == ord("q"):
                break

        cap.release()
        cv2.destroyAllWindows()

        return "Camera closed."

    return None