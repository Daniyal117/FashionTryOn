import io
import os,cv2
import numpy as np 
import uuid
from PIL import Image
from celery_app import celery
from face_crop import process_cropping
from remove_bg import generate_task
from try_on import final_segmentation

@celery.task(bind=True)
def image_processing(self,base_image_bytes,target_image_bytes):
    """
    Processes an image by performing background removal, face cropping, and segmentation.

    Args:
        self: The Celery task instance.
        base_image_bytes (bytes): The byte representation of the base image.
        target_image_bytes (bytes): The byte representation of the target image.

    Workflow:
        1. `generate_task`: Removes the background from the images and returns processed base and target images.
        2. `process_cropping`: Crops the face from the target image.
        3. `final_segmentation`: Performs final segmentation on the processed images.
    """
    base_image,target_image=generate_task(base_image_bytes,target_image_bytes)
    target_image=process_cropping(target_image)
    final_segmentation(base_image,target_image)

