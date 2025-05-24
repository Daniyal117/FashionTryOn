import redis
import time
import jwt
import os
import requests
import base64
from io import BytesIO
from dotenv import load_dotenv

load_dotenv()

# Redis Configuration
REDIS_HOST = "localhost"  
REDIS_PORT = 6379
redis_client = redis.StrictRedis(host=REDIS_HOST, port=REDIS_PORT, db=0, decode_responses=True)

sk = os.environ.get("SECRET_KEY")
ak = os.environ.get("ACCESS_KEY")

def encode_jwt_token():
    """Generate a new JWT token with a 30-minute expiry."""
    headers = {"alg": "HS256", "typ": "JWT"}
    current_time = int(time.time())
    payload = {"iss": ak, "exp": current_time + 1800, "nbf": current_time - 5}
    token = jwt.encode(payload, sk, algorithm="HS256", headers=headers)
    return token, payload["exp"]

def get_valid_token():
    """Retrieve token from Redis if valid, otherwise generate a new one."""
    token = redis_client.get("jwt_token")
    expiry = redis_client.get("jwt_expiry")
    if token and expiry and time.time() < float(expiry):
        return token, float(expiry)
    
    token, expiry = encode_jwt_token()
    redis_client.set("jwt_token", token, ex=1800)
    redis_client.set("jwt_expiry", expiry, ex=1800)
    return token, expiry

def pil_to_base64(pil_image):
    buffer = BytesIO()
    pil_image.save(buffer, format="PNG")
    return base64.b64encode(buffer.getvalue()).decode("utf-8")

def request_task_id(base, target):
    """
    Requests a task ID for virtual try-on image processing.

    Args:
        base (PIL.Image.Image): The base (human) image.
        target (str): Base64-encoded clothing image.

    Returns:
        tuple: (task_id, token, expiry) if successful, otherwise (None, token, expiry).
    """

    url = "https://api.klingai.com/v1/images/kolors-virtual-try-on"  
    token, expiry = get_valid_token()   
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {token}"
    }
    human_image_base64 = pil_to_base64(base)          
    cloth_image_base64 = target 
    
    payload = {
        "model_name": "kolors-virtual-try-on-v1-5",
        "human_image": human_image_base64,
        "cloth_image": cloth_image_base64  
    }
    
    response = requests.post(url, json=payload, headers=headers)
    if response.status_code != 200:
        print("Error requesting task_id:", response.status_code, response.text)
        return None, token, expiry
    response_json = response.json()
    try:
        task_id = response_json['data']['task_id']
        return task_id, token, expiry
    except KeyError:
        print("Unexpected response format:", response_json)
        return None, token, expiry

def query_task_status(task_id):
    """
    Polls the API to check the status of a segmentation task.

    Args:
        task_id (str): The unique identifier of the task.

    Returns:
        dict or None: The task result if successful, None if the task fails or times out.
    """
    
    url = f"https://api.klingai.com/v1/images/kolors-virtual-try-on/{task_id}"
    max_attempts = 60
    attempts = 0
    while attempts < max_attempts:
        token, _ = get_valid_token()
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {token}"
        }
        try:
            response = requests.get(url, headers=headers)
        except Exception as e:
            print(f"Exception during request: {e}")
            return None
        if response.status_code != 200:
            print(f"Failed to query task. Status Code: {response.status_code}")
            print(response.text)
            return None
        result = response.json()
        task_status = result.get("data", {}).get("task_status")
        if not task_status:
            print("Task status not found in response.")
            return None
        print(f"Task Status: {task_status}") 
        if task_status == "succeed":
            return result["data"]["task_result"]
        elif task_status == "failed":
            print("Task failed.")
            return None
        attempts += 1
        time.sleep(3)
    print("Maximum polling attempts reached. Task did not complete in time.")
    return None

def download_image(image_url, save_folder):
    if not os.path.exists(save_folder):
        os.makedirs(save_folder)
    ext = os.path.splitext(image_url)[-1].split('?')[0] 
    if not ext:
        ext = ".png"

    filename = f"final_image{ext}"
    save_path = os.path.join(save_folder, filename)
    if os.path.exists(save_path):
        os.remove(save_path)

    response = requests.get(image_url)
    if response.status_code == 200:
        with open(save_path, "wb") as file:
            file.write(response.content)
        print(f"Image successfully downloaded: {save_path}")
    else:
        print(f"Failed to download image. Status code: {response.status_code}")

def final_segmentation(base, target):
    """
    Performs the final segmentation process and saves the segmented image.

    Args:
        base (str or bytes): The base image data or path.
        target (str or bytes): The target image data or path.

    Workflow:
        1. Requests a task ID for segmentation.
        2. Checks the task status.
        3. Retrieves the segmented image URL upon task completion.
        4. Downloads and saves the segmented image in the "segmented_image" folder.

    Returns:
        None
    """
    save_folder = "segmented_image"
    task_id, _, _ = request_task_id(base, target)
    if task_id:
        result = query_task_status(task_id)
        if result:
            image_url = result['images'][0]['url']
            download_image(image_url, save_folder)
        else:
            print("Task did not complete successfully.")
    else:
        print("Failed to obtain task ID.")
