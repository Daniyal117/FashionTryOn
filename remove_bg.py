import io
import os,cv2
import numpy as np 
import uuid
from PIL import Image
from celery_app import celery
from background_replacer import replace_background
from face_crop import process_cropping
   
def generate_task(base_image_bytes,target_image_bytes):
    """
    Processes images by removing backgrounds and refining edges.

    Args:
        base_image_bytes (bytes): Byte data of the base image.
        target_image_bytes (bytes): Byte data of the target image.

    Returns:
        Processed base and target image, or an error message on failure.
    """

    positive_prompt="Person, clear edges, detailed face, natural skin tone"
    negative_prompt="Background, blur, noise, shadows, unwanted objects, artifacts"
    try:
        base_image_pil = Image.open(io.BytesIO(base_image_bytes)).convert("RGB")
        target_image_pil = Image.open(io.BytesIO(target_image_bytes)).convert("RGB")

        options = {
            'seed': -1,  
            'depth_map_feather_threshold': 128,
            'depth_map_dilation_iterations': 10,
            'depth_map_blur_radius': 10,
        }
        base_results=replace_background(base_image_pil, positive_prompt, negative_prompt, options)
        target_result = replace_background(target_image_pil, positive_prompt, negative_prompt, options)
        base ,target=process_images(target_result,base_results)
        return base,target

    except Exception as e:
        return {"error": str(e)}


def process_images(target_result, base_results):
    try:
        flat_images_target = []
        flat_images_base = []

        if isinstance(target_result, list):
            for item in target_result:
                if isinstance(item, list):  
                    target_result.extend([img for img in item if isinstance(img, Image.Image)])
                elif isinstance(item, Image.Image):
                    flat_images_target.append(item)

        if not flat_images_target:
            raise ValueError("No valid images returned from replace_background.")
        result_target = flat_images_target[2] if len(flat_images_target) >=2 else flat_images_target[0]
        if isinstance(base_results, list):
            for item in base_results:
                if isinstance(item, list):  
                    base_results.extend([img for img in item if isinstance(img, Image.Image)])
                elif isinstance(item, Image.Image):  
                    flat_images_base.append(item)

        if not flat_images_base:
            raise ValueError("No valid images returned from replace_background.")

        result_base = flat_images_base[2] if len(flat_images_base) >=2 else flat_images_base[0]
        return result_base,result_target

    except Exception as e:
        return {"error": str(e)}

