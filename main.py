import io
import base64
import uuid
from fastapi import FastAPI, File, UploadFile
from fastapi.responses import JSONResponse
from PIL import Image
from tasks import image_processing  # Import Celery task
from celery.result import AsyncResult

app = FastAPI()
@app.post("/process-two-images/")
async def process_two_images(
    base_image: UploadFile = File(...),
    target_image: UploadFile = File(...)
):
    """
    API endpoint to process two uploaded images asynchronously.
    Args:
        base_image (UploadFile): The base image file.
        target_image (UploadFile): The target image file.

    Returns:
        JSONResponse: Contains the task ID if successful or an error message if failed.
    """
    try:
        base_image_bytes = await base_image.read()
        target_image_bytes = await target_image.read()
        task = image_processing.delay(base_image_bytes, target_image_bytes)
        return JSONResponse(content={"task_id": task.id, "message": "Processing started"})
    except Exception as e:
        return JSONResponse(content={"error": str(e)}, status_code=500)


@app.get("/task-status/{task_id}")
async def get_task_status(task_id: str):
    """
    API endpoint to check the status of a Celery task.

    Args:
        task_id (str): The unique ID of the Celery task.

    Returns:
        JSONResponse: Contains the task ID, current status, and result (if available).
    """
    task_result = AsyncResult(task_id)

    return JSONResponse(content={
        "task_id": task_id,
        "status": task_result.status,  # PENDING, STARTED, SUCCESS, FAILURE
        "result": task_result.result if task_result.ready() else None
    })
