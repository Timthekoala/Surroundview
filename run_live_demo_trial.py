import os
import cv2
from surround_view import CaptureThread, CameraProcessingThread
from surround_view import FisheyeCameraModel, BirdView
from surround_view import MultiBufferManager, ProjectedImageBuffer
import surround_view.param_settings as settings


yamls_dir = os.path.join(os.getcwd(), "yaml")
camera_ids = [0, 2, 8, 6]
flip_methods = [0, 0, 2, 2]
names = settings.camera_names
cameras_files = [os.path.join(yamls_dir, name + ".yaml") for name in names]
camera_models = [FisheyeCameraModel(camera_file, name) for camera_file, name in zip(cameras_files, names)]
fourcc = cv2.VideoWriter_fourcc(*'YUY2')
stream = cv2.VideoWriter("appsrc ! x264enc ! h264parse ! rtph264pay config-interval=1 pt=96 ! autovideosink", fourcc, 30, (1280,720))

def main():
    capture_tds = [CaptureThread(camera_id, flip_method, resolution=(640,480), use_gst=False)
                   for camera_id, flip_method in zip(camera_ids, flip_methods)]
    capture_buffer_manager = MultiBufferManager()
    for td in capture_tds:
        capture_buffer_manager.bind_thread(td, buffer_size=8)
        if (td.connect_camera()):
            td.start()

    proc_buffer_manager = ProjectedImageBuffer()
    process_tds = [CameraProcessingThread(capture_buffer_manager,
                                          camera_id,
                                          camera_model)
                   for camera_id, camera_model in zip(camera_ids, camera_models)]
    for td in process_tds:
        proc_buffer_manager.bind_thread(td)
        td.start()

    birdview = BirdView(proc_buffer_manager)
    birdview.load_weights_and_masks("./weights.png", "./masks.png")
    birdview.start()
    while True:
        img = cv2.resize(birdview.get(), (600, 800))
        #cv2.imshow("birdview", img)
        stream.write(img)
        key = cv2.waitKey(1) & 0xFF
        if key == ord("q"):
            break

        for td in capture_tds:
            print("camera {} fps: {}\n".format(td.device_id, td.stat_data.average_fps), end="\r")

        for td in process_tds:
            print("process {} fps: {}\n".format(td.device_id, td.stat_data.average_fps), end="\r")

        print("birdview fps: {}".format(birdview.stat_data.average_fps))

    stream.release()
    cv2.destroyAllWindows()

    for td in process_tds:
        td.stop()

    for td in capture_tds:
        td.stop()
        td.disconnect_camera()


if __name__ == "__main__":
    main()