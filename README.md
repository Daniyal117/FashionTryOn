# Virtual Try-On API

## 📌 Overview
This API allows users to virtually try on clothing. The system takes two images as input:
1. **Person Image** – The image of the person who wants to try on clothes.
2. **Clothing Image** – Either an image of a standalone piece of clothing or a person wearing the clothing.

### 🛠 Process
1. **Remove Background** – The backgrounds of both images are removed.
2. **Head Cropping (if applicable)** – If the clothing image is of a person, the head is cropped.
3. **Virtual Try-On** – The processed images are sent to the Try-On API to generate the final output, showing the person wearing the clothing.

---

### Example Results

Here are some example results from our Virtual Try-On API:

#### Input Images
![Input Images](results/input_try_on.png)
*Left: Person Image | Right: Clothing Image*

#### Target Clothing
![Target Clothing](results/target_try_on.png)
*Target clothing item used in the try-on*

#### Output Result
![Output Result](results/result2.png)
*Final Result: Person wearing the selected clothing item*

## 🚀 Setup Instructions

### 1️⃣ Create & Activate Virtual Environment

Before installing dependencies, create a virtual environment:

#### For Windows:
```bash
python -m venv venv
venv\Scripts\activate
```

#### For macOS/Linux:
```bash
python3 -m venv venv
source venv/bin/activate
```

---

### 2️⃣ Install Dependencies
Once the virtual environment is activated, install the required dependencies:

```bash
pip install -r requirements.txt
```

---

### 3️⃣ Start Redis Server
Redis is required for Celery task management. Run:

```bash
redis-server
```

---

### 4️⃣ Start FastAPI Server
Run the FastAPI application using:

```bash
uvicorn main:app --reload
```

---

### 5️⃣ Start Celery Worker
Run the Celery worker to process background tasks:

```bash
PYTHONPATH=$(pwd) celery -A tasks worker --loglevel=info --pool=threads
```

---

## 📡 API Endpoints

### 1️⃣ Process Images

**Endpoint:**
```http
POST /process-two-images/
```

**Description:**  
Uploads two images and starts processing them.

**Request Example (Multipart Form-Data):**
```http
{
    "base_image": <person_image.jpg>,
    "target_image": <clothing_image.jpg>
}
```

**Response:**
```json
{
    "task_id": "12345abcde",
    "message": "Processing started"
}
```

---

### 2️⃣ Check Task Status

**Endpoint:**
```http
GET /task-status/{task_id}
```

**Description:**  
Checks the processing status of an image processing task.

**Response Example (In Progress):**
```json
{
    "task_id": "12345abcde",
    "status": "PENDING",
    "result": null
}
```

**Response Example (Completed):**
```json
{
    "task_id": "12345abcde",
    "status": "SUCCESS",
    "result": {
        "images": [
            {"url": "https://yourserver.com/segmented_image.jpg"}
        ]
    }
}
```

## 🎯 Results Showcase


### Key Features Demonstrated
- ✅ Accurate clothing placement
- ✅ Natural body pose preservation
- ✅ High-quality image output
- ✅ Realistic fabric rendering
- ✅ Seamless integration with body shape

---

## 📞 Contact & Support
For any questions or support, please open an issue in this repository.
