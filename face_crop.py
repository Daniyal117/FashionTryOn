import cv2
import numpy as np
import mediapipe as mp
import base64
import os
mp_face_detection = mp.solutions.face_detection

def face_detect_and_crop(image):
    """
    Detects a face in the image and crops the body below it.
    
    Args:
        image (numpy.ndarray): The input image in BGR format.

    Returns:
        str: Base64-encoded cropped image. If no face is detected, returns the full image.
    
    Raises:
        ValueError: If the input image is invalid.
    """
    if image is None:
        raise ValueError("Invalid image input. Ensure the image is correctly passed.")
    convert_color = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
    with mp_face_detection.FaceDetection(min_detection_confidence=0.5) as face_detection:
        results = face_detection.process(convert_color)
        if results.detections:
            for detection in results.detections:
                boundary_box = detection.location_data.relative_bounding_box
                x, y, w, h = (
                    int(boundary_box.xmin * image.shape[1]),
                    int(boundary_box.ymin * image.shape[0]),
                    int(boundary_box.width * image.shape[1]),
                    int(boundary_box.height * image.shape[0])
                )
                x, y = max(0, x), max(0, y)
                w, h = min(image.shape[1] - x, w), min(image.shape[0] - y, h)
                body_image = image[y + h:, :]
                break 
        else:
            body_image = image  
    _, buffer = cv2.imencode(".jpg", body_image)
    base64_encoded_data = base64.b64encode(buffer).decode("utf-8")
    return base64_encoded_data

def process_cropping(target_image):
    """
    Detects and crops the face from the target image.

    Args:
        target_image (PIL.Image.Image): The target image to process.

    Returns:
        str: The base64-encoded cropped image.
    """
    image=cv2.cvtColor(np.array(target_image), cv2.COLOR_RGB2BGR)
    processed_image_base64= face_detect_and_crop(image)
    return processed_image_base64

