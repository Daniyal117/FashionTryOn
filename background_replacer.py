import warnings
warnings.filterwarnings("ignore", category=FutureWarning)  # nopep8
warnings.filterwarnings("ignore", category=UserWarning)  # nopep8
import os
import math
from tqdm import tqdm
import torch
from PIL import Image, ImageFilter
from scipy.ndimage import binary_dilation
import numpy as np
from captioner import init as init_captioner, derive_caption
from upscaler import init as init_upscaler
from segmenter import init as init_segmenter, segment
from depth_estimator import init as init_depth_estimator, get_depth_map
from pipeline import init as init_pipeline, run_pipeline
from image_utils import ensure_resolution, crop_centered

developer_mode = os.getenv('DEV_MODE', False)
init_pipeline()
POSITIVE_PROMPT_SUFFIX = "commercial product photography, 24mm lens f/8"
NEGATIVE_PROMPT_SUFFIX = "cartoon, drawing, anime, semi-realistic, illustration, painting, art, text, greyscale, (black and white), lens flare, watermark, cropped, out of frame, worst quality, low quality, jpeg artifacts, ugly, duplicate, morbid, mutilated, extra fingers, mutated hands, poorly drawn hands, poorly drawn face, mutation, deformed, dehydrated, bad anatomy, bad proportions, extra limbs, cloned face, disfigured, gross proportions, malformed limbs, missing arms, missing legs, extra arms, extra legs, fused fingers, too many fingers, long neck, floating, levitating"

MEGAPIXELS = 1.0


def replace_background(
    original,
    positive_prompt,
    negative_prompt,
    options,
):
    pbar = tqdm(total=7)

    print("Original size:", original.size)

    print("Captioning...")
    init_captioner()
    caption = derive_caption(original)
    pbar.update(1)

    print("Caption:", caption)

    torch.cuda.empty_cache()

    print(f"Ensuring resolution ({MEGAPIXELS}MP)...")
    resized = ensure_resolution(original, megapixels=MEGAPIXELS)
    pbar.update(1)

    print("Resized size:", resized.size)

    torch.cuda.empty_cache()

    print("Segmenting...")
    init_segmenter()
    [cropped, crop_mask] = segment(resized)
    pbar.update(1)

    torch.cuda.empty_cache()

    print("Depth mapping...")
    init_depth_estimator()
    depth_map = get_depth_map(resized)
    pbar.update(1)

    torch.cuda.empty_cache()
    print("Feathering the depth map...")
    crop_mask_np = np.array(crop_mask.convert('L'))
    crop_mask_binary = crop_mask_np > options.get(
        'depth_map_feather_threshold')
    dilated_mask = binary_dilation(
        crop_mask_binary, iterations=options.get('depth_map_dilation_iterations'))

    dilated_mask = Image.fromarray((dilated_mask * 255).astype(np.uint8))

 
    dilated_mask_blurred = dilated_mask.filter(
        ImageFilter.GaussianBlur(radius=options.get('depth_map_blur_radius')))
    dilated_mask_blurred_np = np.array(dilated_mask_blurred) / 255.0

    depth_map_np = np.array(depth_map.convert('L')) / 255.0
    masked_depth_map_np = depth_map_np * dilated_mask_blurred_np
    masked_depth_map_np = (masked_depth_map_np * 255).astype(np.uint8)

    masked_depth_map = Image.fromarray(masked_depth_map_np).convert('RGB')

    pbar.update(1)

    final_positive_prompt = f"{caption}, {positive_prompt}, {POSITIVE_PROMPT_SUFFIX}"
    final_negative_prompt = f"{negative_prompt}, {NEGATIVE_PROMPT_SUFFIX}"

    print("Final positive prompt:", final_positive_prompt)
    print("Final negative prompt:", final_negative_prompt)

    print("Generating...")

    generated_images = run_pipeline(
        positive_prompt=final_positive_prompt,
        negative_prompt=final_negative_prompt,
        image=[masked_depth_map],
        seed=options.get('seed')
    )
    pbar.update(1)

    torch.cuda.empty_cache()

    print("Compositing...")

    composited_images = [
        Image.alpha_composite(
            generated_image.convert('RGBA'),
            crop_centered(cropped, generated_image.size)
        ) for generated_image in generated_images
    ]
    pbar.update(1)
    pbar.close()

    print("Done!")

    if developer_mode:
        pre_processing_images = [
            [resized, "Resized"],
            [crop_mask, "Crop mask"],
            [cropped, "Cropped"],
            [depth_map, "Depth map"],
            [dilated_mask, "Dilated mask"],
            [dilated_mask_blurred, "Dilated mask blurred"],
            [masked_depth_map, "Masked depth map"]
        ]
        return [
            composited_images,
            generated_images,
            pre_processing_images,
            caption,
        ]
    else:
        return [composited_images, None, None, None]
