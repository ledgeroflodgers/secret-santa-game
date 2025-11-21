# Usage

- Admin pass: fx
- Reset pass: saeed
- http://secret-santa-frontend-dev-605868565364.s3-website-us-east-1.amazonaws.com

# Secret Santa Game

A web-based Secret Santa game application with Angular frontend and Flask backend, deployable to AWS (S3 + Lambda).

## Quick Links

- [Quick Start Guide](QUICKSTART.md) - Get started in 5 minutes
- [Deployment Guide](docs/DEPLOYMENT.md) - Complete AWS deployment instructions
- [Backend README](secret-santa-backend/README.md) - Backend API documentation

## Project Structure

```
secret-santa/
├── secret-santa-frontend/          # Angular frontend application
│   ├── src/
│   │   ├── app/
│   │   │   ├── admin/             # Admin component
│   │   │   ├── home/              # Home page component
│   │   │   ├── participants/      # Participants list
│   │   │   ├── registration/      # Registration form
│   │   │   ├── services/          # API services
│   │   │   └── ...
│   │   ├── environments/          # Environment configs
│   │   └── ...
│   └── package.json
├── secret-santa-backend/           # Flask backend API
│   ├── app.py                     # Main Flask application
│   ├── lambda_handler.py          # AWS Lambda handler
│   ├── database.py                # File-based database
│   ├── s3_database.py             # S3-based database for Lambda
│   ├── models.py                  # Data models
│   ├── template.yaml              # AWS SAM template
│   ├── requirements.txt           # Python dependencies
│   └── README.md
├── deploy-backend.sh               # Backend deployment script
├── deploy-frontend.sh              # Frontend deployment script
├── deploy-all.sh                   # Complete deployment script
├── DEPLOYMENT.md                   # Detailed deployment guide
├── QUICKSTART.md                   # Quick start guide
└── README.md
```

## Development Setup

### Backend (Flask)

1. Navigate to the backend directory:
```bash
cd secret-santa-backend
```

2. Create and activate a virtual environment:
```bash
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Run the Flask server:
```bash
python3 app.py
```

The backend will be available at http://localhost:5000

### Frontend (Angular)

1. Navigate to the frontend directory:
```bash
cd secret-santa-frontend
```

2. Install dependencies:
```bash
npm install
```

3. Start the development server:
```bash
npm start
```

The frontend will be available at http://localhost:4200

## Features

- **Participant Registration**: Users can register to join the Secret Santa game
- **Gift Management**: Add and manage gifts in the pool
- **Turn-based Gameplay**: Fair turn order with gift selection mechanics
- **Real-time Updates**: Live game state updates
- **CORS Enabled**: Frontend and backend communication configured

## API Endpoints

- `GET /api/health` - Health check endpoint
- Additional endpoints will be implemented in subsequent tasks

## Technology Stack

- **Frontend**: Angular 16, TypeScript, CSS
- **Backend**: Flask, Python
- **Data Storage**: JSON file with file locking (local) or S3 (AWS)
- **HTTP Client**: Angular HttpClient with CORS support
- **AWS Services**: Lambda, API Gateway, S3, CloudFormation

## Deployment

### Local Development

See [QUICKSTART.md](QUICKSTART.md) for local development setup.

### AWS Deployment

Deploy to AWS with a single command:

```bash
./deploy-all.sh dev
```

This deploys:
- Angular frontend to S3 with static website hosting
- Flask backend to AWS Lambda
- API Gateway for RESTful endpoints
- S3 bucket for data persistence

For detailed deployment instructions, see [DEPLOYMENT.md](docs/DEPLOYMENT.md).

## Architecture

### Local Development
- Frontend: Angular dev server (localhost:4200)
- Backend: Flask dev server (localhost:8080)
- Database: JSON file with file locking

### AWS Production
- Frontend: S3 static website hosting
- Backend: AWS Lambda + API Gateway
- Database: JSON file in S3 with versioning

## Game Features

- **Participant Registration**: Up to 100 participants with unique number assignment
- **Gift Management**: Add gifts to the pool with steal tracking
- **Gift Stealing**: Participants can steal gifts with a 3-steal lock mechanism
- **Turn Management**: Fair turn-based gameplay with admin controls
- **Real-time Updates**: Live participant and gift status updates
- **Concurrent Safety**: Atomic operations prevent race conditions
- **Reset**: Admin can reset entire game state