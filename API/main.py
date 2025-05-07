from fastapi import FastAPI, HTTPException, Depends, status, File, UploadFile
from fastapi.security import OAuth2PasswordRequestForm
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from datetime import timedelta
import google.generativeai as genai
from dotenv import load_dotenv
import os

import models
import schemas
import security
from database import engine, get_db
from detection_utils import initialize_detector, get_detector

# Create database tables
models.Base.metadata.create_all(bind=engine)

# Load environment variables
load_dotenv()

# Initialize the image detector
MODEL_PATH = os.path.join(os.path.dirname(__file__), "my_model.h5")  # Use relative path from API folder
print(f"Looking for model at: {MODEL_PATH}")

if not os.path.exists(MODEL_PATH):
    print(f"Warning: Model file not found at {MODEL_PATH}")
    print("The /detect endpoint will not be available until a valid model is provided.")
else:
    try:
        print("Attempting to load model...")
        initialize_detector(MODEL_PATH)
        print(f"Model initialized successfully from {MODEL_PATH}")
    except Exception as e:
        print(f"Warning: Could not initialize detector: {str(e)}")
        print("The /detect endpoint will not be available until the model is properly initialized.")

# Configure Gemini AI
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
print(GEMINI_API_KEY)

if not GEMINI_API_KEY:
    raise ValueError("GEMINI_API_KEY not found in environment variables")

genai.configure(api_key=GEMINI_API_KEY)

# List available models to verify access
try:
    for m in genai.list_models():
        if 'generateContent' in m.supported_generation_methods:
            print(f"Found model: {m.name}")
except Exception as e:
    print(f"Error listing models: {str(e)}")

# Initialize the model with safety settings
generation_config = {
    "temperature": 0.9,
    "top_p": 1,
    "top_k": 1,
    "max_output_tokens": 2048,
}

safety_settings = [
    {"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_MEDIUM_AND_ABOVE"},
    {"category": "HARM_CATEGORY_HATE_SPEECH", "threshold": "BLOCK_MEDIUM_AND_ABOVE"},
    {"category": "HARM_CATEGORY_SEXUALLY_EXPLICIT", "threshold": "BLOCK_MEDIUM_AND_ABOVE"},
    {"category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "BLOCK_MEDIUM_AND_ABOVE"},
]

try:
    model = genai.GenerativeModel(model_name="gemini-2.0-flash-001",
                                generation_config=generation_config,
                                safety_settings=safety_settings)
except Exception as e:
    print(f"Error initializing Gemini model: {str(e)}")
    raise

app = FastAPI(
    title="FastAPI with Gemini AI and Image Detection",
    description="A FastAPI application that integrates with Google's Gemini AI and provides image detection",
    version="1.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, replace with specific origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# User management endpoints
@app.post("/register", response_model=schemas.User)
def register_user(user: schemas.UserCreate, db: Session = Depends(get_db)):
    db_user = db.query(models.User).filter(models.User.email == user.email).first()
    if db_user:
        raise HTTPException(status_code=400, detail="Email already registered")
    
    db_user = db.query(models.User).filter(models.User.username == user.username).first()
    if db_user:
        raise HTTPException(status_code=400, detail="Username already taken")
    
    hashed_password = security.get_password_hash(user.password)
    db_user = models.User(
        email=user.email,
        username=user.username,
        hashed_password=hashed_password
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user

@app.post("/token", response_model=schemas.Token)
async def login(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    user = db.query(models.User).filter(models.User.email == form_data.username).first()
    if not user or not security.verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token_expires = timedelta(minutes=security.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = security.create_access_token(
        data={"sub": user.email}, expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}

@app.get("/users/me", response_model=schemas.User)
async def read_users_me(current_user: models.User = Depends(security.get_current_user)):
    return current_user

# Chat endpoint (now requires authentication)
@app.post("/chat", response_model=schemas.ChatResponse)
async def chat(
    request: schemas.ChatRequest,
    current_user: models.User = Depends(security.get_current_user)
):
    try:
        response = model.generate_content(request.message)
        if response.text:
            return schemas.ChatResponse(response=response.text)
        else:
            raise HTTPException(status_code=500, detail="No response generated")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Updated image detection endpoint
@app.post("/detect", response_model=schemas.ChatResponse)
async def detect_image(
    file: UploadFile = File(...),
    current_user: models.User = Depends(security.get_current_user)
):
    """
    Detect objects in the uploaded image using the loaded model.
    """
    # Validate file
    if not file:
        raise HTTPException(
            status_code=400,
            detail="No file uploaded"
        )
    
    # Check file content type
    if not file.content_type:
        raise HTTPException(
            status_code=400,
            detail="File content type is missing"
        )
    
    if not file.content_type.startswith('image/'):
        raise HTTPException(
            status_code=400,
            detail=f"Invalid file type: {file.content_type}. Only image files are allowed."
        )
    
    # Check file size (optional, adjust limit as needed)
    file_size = 0
    try:
        file_size = len(await file.read())
        await file.seek(0)  # Reset file pointer
    except Exception as e:
        raise HTTPException(
            status_code=400,
            detail=f"Error reading file: {str(e)}"
        )
    
    if file_size > 10 * 1024 * 1024:  # 10MB limit
        raise HTTPException(
            status_code=400,
            detail="File size exceeds 10MB limit"
        )
        
    try:
        # Check if model is available
        if not os.path.exists(MODEL_PATH):
            raise HTTPException(
                status_code=503,
                detail="Model file not found. Please ensure my_model.h5 exists in the API folder."
            )
            
        # Read the image file
        try:
            image_data = await file.read()
        except Exception as e:
            raise HTTPException(
                status_code=400,
                detail=f"Error reading image file: {str(e)}"
            )
        
        # Get the detector
        try:
            detector = get_detector()
        except Exception as e:
            raise HTTPException(
                status_code=503,
                detail=f"Model initialization error: {str(e)}"
            )
        
        # Perform detection
        try:
            predictions, confidence_scores, processing_time = detector.predict(image_data)
            answer = "Hay giup toi dua ra loi khuyen cho can benh "
            if predictions[0]['class_name'] == "class_7":
                answer += "shingles"
            elif predictions[0]['class_name'] == "class_2":
                answer += "dd"
            elif predictions[0]['class_name'] == "class_3":
                answer += "dd"
            else:
                answer += "dd"
        except Exception as e:
            raise HTTPException(
                status_code=500,
                detail=f"Error processing image: {str(e)}"
            )
            
        response = model.generate_content(answer)
        if response.text:
            return schemas.ChatResponse(response=response.text)
        else:
            raise HTTPException(status_code=500, detail="No response generated")

        # return schemas.DetectionResponse(
        #     predictions=predictions,
        #     confidence_scores=confidence_scores,
        #     processing_time=processing_time,
        #     answer=answer
        # )
        
    except HTTPException as he:
        raise he
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"An unexpected error occurred: {str(e)}"
        )

@app.get("/")
async def root():
    return {"message": "Welcome to FastAPI with Gemini AI and User Management"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000) 