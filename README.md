# Auth0-Cognito Login System

A secure authentication system demonstrating integration of AWS Cognito and Auth0 with account linking capabilities.

## Features

- **Dual Authentication Flows**:
  - AWS Cognito federated with Auth0 (OIDC)
  - Direct Auth0 authentication
- **Account Linking**: Users can link multiple identity providers to a single account
- **Secure Token Management**: JWT access tokens (in-memory) + httpOnly refresh tokens
- **Modern Stack**: FastAPI backend + React.js frontend
- **Production-Ready**: Docker Compose deployment with PostgreSQL

## Prerequisites

- Docker and Docker Compose
- AWS Cognito User Pool (with Auth0 federation configured)
- Auth0 Accounts

## Setup Instructions

### 1. Clone and Configure

```bash
git clone <repository-url>
cd auth0-cognito-login
```

### 2. Environment Variables

Copy the example environment file and fill in your credentials:

```bash
cp .env.example .env
```

Edit `.env` with your actual values:

```bash
# Generate secure keys
python -c "import secrets; print(secrets.token_urlsafe(32))"
```

Required configurations:
- `JWT_SECRET_KEY`: Your generated secret key
- `COGNITO_*`: AWS Cognito User Pool details
- `AUTH0_RESEARCH_*`: Auth0 tenant details
- `DB_PASSWORD`: Secure database password

### 3. AWS Cognito Configuration

#### Create User Pool

1. Go to AWS Cognito Console
2. Create a new User Pool
3. Configure email as username
4. Create an App Client with client secret
5. Configure Hosted UI domain

#### Add Auth0 as OIDC Identity Provider

1. In your User Pool, go to "Sign-in experience" → "Federated identity provider sign-in"
2. Add OIDC provider:
   - **Provider name**: Auth0-Fashion
   - **Client ID**: From Auth0 Fashion application
   - **Client secret**: From Auth0 Fashion application
   - **Issuer URL**: `https://<your-Fashion-domain>.auth0.com/`
   - **Scopes**: `openid email profile`
   - **Attribute mapping**:
     - email → email
     - sub → username

3. In App client settings:
   - Enable Authorization code grant
   - Set callback URL: `http://localhost:8000/api/v1/auth/callback/cognito`
   - Enable the Auth0-Fashion identity provider

### 4. Auth0 Configuration

#### Fashion Tenant

1. Create a Regular Web Application
2. Add Allowed Callback URLs: Your Cognito callback URL
3. Note the Domain, Client ID, and Client Secret

#### Research Catalog Tenant

1. Create a Regular Web Application
2. Set Allowed Callback URLs: `http://localhost:8000/api/v1/auth/callback/auth0`
3. Set Allowed Logout URLs: `http://localhost:3000/login`
4. Note the Domain, Client ID, and Client Secret

### 5. Run with Docker Compose

```bash
# Build and start all services
docker-compose up --build

# Or run in detached mode
docker-compose up -d --build
```

Services will be available at:
- Frontend: http://localhost:3000
- Backend API: http://localhost:8000
- API Documentation: http://localhost:8000/docs
- PostgreSQL: localhost:5432

### 6. Database Migrations

Run migrations inside the backend container:

```bash
docker-compose exec backend alembic upgrade head
```

## Project Structure

```
auth0-cognito-login/
├── backend/                    # FastAPI Backend
│   ├── app/
│   │   ├── main.py            # FastAPI app initialization
│   │   ├── config.py          # Environment configuration
│   │   ├── database.py        # SQLAlchemy setup
│   │   ├── models/            # Database models
│   │   ├── schemas/           # Pydantic schemas
│   │   ├── services/          # Business logic
│   │   │   ├── cognito_service.py
│   │   │   ├── auth0_service.py
│   │   │   ├── jwt_service.py
│   │   │   ├── user_service.py
│   │   │   └── link_service.py
│   │   ├── routers/           # API endpoints
│   │   │   ├── auth.py
│   │   │   ├── user.py
│   │   │   └── link.py
│   │   ├── dependencies/      # Dependency injection
│   │   └── utils/             # Utilities
│   ├── alembic/               # Database migrations
│   ├── requirements.txt
│   └── Dockerfile
│
├── frontend/                   # React Frontend
│   ├── src/
│   │   ├── App.js             # Main app component
│   │   ├── index.js           # Entry point
│   │   ├── context/           # React Context
│   │   │   └── AuthContext.js
│   │   ├── pages/             # Page components
│   │   │   ├── LoginPage.js
│   │   │   ├── CallbackPage.js
│   │   │   └── HomePage.js
│   │   ├── components/        # Reusable components
│   │   │   └── Auth/
│   │   │       └── ProtectedRoute.js
│   │   ├── services/          # API services
│   │   │   ├── api.js
│   │   │   ├── authService.js
│   │   │   └── userService.js
│   │   └── utils/
│   │       └── tokenManager.js
│   ├── package.json
│   └── Dockerfile
│
├── docker-compose.yml
├── .env.example
└── README.md
```

## API Endpoints

### Authentication

- `POST /api/v1/auth/login/cognito` - Initiate Cognito OAuth flow
- `POST /api/v1/auth/login/auth0` - Initiate Auth0 OAuth flow
- `GET /api/v1/auth/callback/cognito` - Handle Cognito callback
- `GET /api/v1/auth/callback/auth0` - Handle Auth0 callback
- `POST /api/v1/auth/refresh` - Refresh access token
- `POST /api/v1/auth/logout` - Logout and revoke tokens

### User (Protected)

- `GET /api/v1/user/profile` - Get user profile with linked accounts

### Account Linking (Protected)

- `POST /api/v1/link/start/{provider}` - Start account linking
- `GET /api/v1/link/callback/{provider}` - Complete account linking
- `DELETE /api/v1/link/{provider}` - Unlink account

### Health

- `GET /api/v1/health` - Health check

## Security Features

### Token Management

- **Access Tokens**:
  - Stored in memory only (prevents XSS attacks)
  - Short-lived (15 minutes)
  - JWT format with user claims

- **Refresh Tokens**:
  - Stored in httpOnly cookies (prevents XSS)
  - Long-lived (7 days)
  - Hashed in database (SHA256)
  - Automatic rotation on refresh

### Logout Flow

1. Frontend calls logout endpoint
2. Backend revokes refresh token in database
3. Backend calls Cognito/Auth0 revocation endpoints
4. httpOnly cookie cleared
5. In-memory access token cleared
6. User redirected to login

### CSRF Protection

- OAuth2 state parameter with cryptographic verification
- CORS configured for specific origins
- SameSite=Strict cookie attribute

### Input Validation

- Pydantic schemas validate all inputs
- SQLAlchemy ORM prevents SQL injection
- Email normalization (lowercase)

## Development

### Backend Development

```bash
cd backend

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Run development server
uvicorn app.main:app --reload
```

### Frontend Development

```bash
cd frontend

# Install dependencies
npm install

# Run development server
npm start
```

### Database Migrations

```bash
# Create new migration
cd backend
alembic revision --autogenerate -m "description"

# Apply migrations
alembic upgrade head

# Rollback
alembic downgrade -1
```

## Testing

### Manual Testing Flow

1. Navigate to http://localhost:3000
2. Click "Fashion Login" or "Research Catalog Login"
3. Authenticate with provider
4. Verify redirect to home page with user profile
5. Test logout functionality
6. Test account linking (login with one provider, link another)

## Troubleshooting

### Database Connection Issues

```bash
# Check if PostgreSQL is running
docker-compose ps

# View database logs
docker-compose logs db

# Restart database
docker-compose restart db
```

### Backend Issues

```bash
# View backend logs
docker-compose logs backend

# Restart backend
docker-compose restart backend

# Check environment variables
docker-compose exec backend env | grep COGNITO
```

### Frontend Issues

```bash
# View frontend logs
docker-compose logs frontend

# Rebuild frontend
docker-compose up -d --build frontend
```

### Token Issues

- Clear browser cookies
- Clear localStorage/sessionStorage
- Check JWT expiration in backend logs
- Verify refresh token in database

## Production Deployment

Before deploying to production:

1. **Generate New Secrets**:
   ```bash
   python -c "import secrets; print(secrets.token_urlsafe(32))"
   ```

2. **Update Environment**:
   - Set `APP_ENV=production`
   - Use HTTPS URLs for all callbacks
   - Update CORS_ORIGINS to production domain

3. **Database**:
   - Use managed PostgreSQL (AWS RDS, etc.)
   - Enable SSL connections
   - Regular backups

4. **Monitoring**:
   - Setup logging aggregation
   - Configure error tracking
   - Health check monitoring

5. **Security**:
   - Enable rate limiting
   - Use secrets manager (AWS Secrets Manager, etc.)
   - Regular security audits

## Tech Stack

- **Backend**: Python 3.11, FastAPI, SQLAlchemy, Alembic
- **Frontend**: React 18, React Router, Axios
- **Database**: PostgreSQL 15
- **Authentication**: AWS Cognito, Auth0, JWT
- **Deployment**: Docker, Docker Compose

## License

MIT

## Author

Built to demonstrate full-stack authentication expertise with AWS Cognito and Auth0 integration.
