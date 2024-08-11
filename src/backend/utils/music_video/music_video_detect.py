import cv2
from scenedetect import SceneManager, open_video, ContentDetector


def find_scenes(video_path):
    video = open_video(video_path)
    scene_manager = SceneManager()
    scene_manager.add_detector(
        ContentDetector(threshold=40))
    scene_manager.detect_scenes(video)
    return scene_manager.get_scene_list()


def detect_movement(video_path, skip_frames, check_duration, threshold=25):
    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        print(f"Error: Could not open video {video_path}")
        return None

    # Get video properties
    fps = cap.get(cv2.CAP_PROP_FPS)
    total_frames = cap.get(cv2.CAP_PROP_FRAME_COUNT)
    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))

    short_side = min(width, height)
    padding = short_side // 4

    start_check = int((fps * check_duration) / skip_frames)
    center_frame_num = int(total_frames // 2)
    center_check = int(center_frame_num / skip_frames) - start_check // 2

    def frame_has_movement(frame1, frame2):
        # Only consider the center part
        center_frame1 = frame1[padding:-padding, padding:-padding]
        center_frame2 = frame2[padding:-padding, padding:-padding]

        gray1 = cv2.cvtColor(center_frame1, cv2.COLOR_BGR2GRAY)
        gray2 = cv2.cvtColor(center_frame2, cv2.COLOR_BGR2GRAY)

        diff = cv2.absdiff(gray1, gray2)
        _, thresh = cv2.threshold(diff, threshold, 255, cv2.THRESH_BINARY)
        movement = cv2.countNonZero(thresh)
        return movement > 0

    frame_count = 0
    prev_frame = None

    movement_detected = False
    while True:
        ret, frame = cap.read()
        if not ret:
            break

        if frame_count % skip_frames == 0:
            if frame_count >= start_check and frame_count < (start_check + fps * check_duration):
                if prev_frame is not None and frame_has_movement(prev_frame, frame):
                    movement_detected = True
                    break

            if frame_count >= center_check and frame_count < (center_check + fps * check_duration):
                if prev_frame is not None and frame_has_movement(prev_frame, frame):
                    movement_detected = True
                    break

            prev_frame = frame

        frame_count += 1

        if frame_count > (start_check + fps * 2 * check_duration):
            break

    cap.release()
    if not movement_detected:
        return False

    scene_list = find_scenes(video_path)
    min_scene_changes = total_frames / fps / 35
    return len(scene_list) > min_scene_changes
