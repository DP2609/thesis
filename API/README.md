# FastAPI with Gemini AI

This is a FastAPI application that integrates with Google's Gemini AI to provide chat functionality.

## Setup

1. Install the required dependencies:
```bash
pip install -r requirements.txt
```

2. Get your Gemini API key from [Google AI Studio](https://makersuite.google.com/app/apikey)

3. Update the `.env` file with your Gemini API key:
```
GEMINI_API_KEY=your_api_key_here
```

## Running the Application

Start the server with:
```bash
python main.py
```

The application will be available at `http://localhost:8000`

## API Endpoints

- `GET /`: Welcome message
- `POST /chat`: Send a message to Gemini AI
  - Request body: `{"message": "Your message here"}`
  - Response: `{"response": "AI response here"}`

## API Documentation

Once the server is running, you can access:
- Swagger UI documentation at `http://localhost:8000/docs`
- ReDoc documentation at `http://localhost:8000/redoc` 