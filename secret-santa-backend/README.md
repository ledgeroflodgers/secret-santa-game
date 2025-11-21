# Secret Santa Backend

Flask backend for the Secret Santa game application.

## Setup

1. Create a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Run the application:
```bash
python app.py
```

The server will start on http://localhost:5000

## API Endpoints

- `GET /api/health` - Health check endpoint

## Data Storage

The application uses a JSON file (`game_data.json`) for data persistence with file locking for concurrent access safety.