import cv2, time

for backend_name, backend in [
    ("DSHOW", cv2.CAP_DSHOW),
    ("MSMF", cv2.CAP_MSMF),
    ("ANY", cv2.CAP_ANY),
]:
    t0 = time.perf_counter()
    cap = cv2.VideoCapture(0, backend)
    ok_open = cap.isOpened()
    t1 = time.perf_counter()

    ok_read, frame = cap.read() if ok_open else (False, None)
    t2 = time.perf_counter()

    cap.release()

    print(
        backend_name,
        "open=", round(t1 - t0, 3),
        "first_read=", round(t2 - t1, 3),
        "ok=", ok_open,
        ok_read,
        "shape=", None if frame is None else frame.shape,
    )