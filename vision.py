import cv2
from ultralytics import YOLO
from voice import speak

model = YOLO("yolov8n.pt")

camera_active = False


def start_vision():

    global camera_active
    camera_active = True

    cap = cv2.VideoCapture(0)

    speak("Vision system activated.")

    while camera_active:

        ret, frame = cap.read()
        if not ret:
            break

        results = model(frame)

        objects_detected = []

        for r in results:
            boxes = r.boxes

            for box in boxes:
                cls = int(box.cls[0])
                name = model.names[cls]

                objects_detected.append(name)

                x1,y1,x2,y2 = map(int,box.xyxy[0])

                cv2.rectangle(frame,(x1,y1),(x2,y2),(0,255,255),2)
                cv2.putText(frame,name,(x1,y1-10),
                            cv2.FONT_HERSHEY_SIMPLEX,
                            0.7,(0,255,255),2)

        cv2.imshow("JARVIS Vision", frame)

        if cv2.waitKey(1) & 0xFF == 27:
            break

    cap.release()
    cv2.destroyAllWindows()


def stop_vision():
    global camera_active
    camera_active = False