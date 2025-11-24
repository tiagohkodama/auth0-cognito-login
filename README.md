# auth0-cognito-login

Issue: Build POC app demonstrating Auth0 + AWS Cognito authentication (React + Python + Docker)

---

> You are a senior full-stack engineer.

Follow the specification in this issue exactly.

Do not introduce new features beyond what is required.

Keep the implementation small, clear, and focused on:

Auth0 login on the frontend.

JWT validation on the backend.

AWS Cognito integration using AWS credentials.

Dockerized local environment.


Avoid complex abstractions; prioritize readability and explicitness.

Where tradeoffs exist, prefer simplicity and clarity over cleverness.


---

0. Purpose & Scope

Build a small, simple, but production-style POC that clearly demonstrates:

A React frontend with:

Login via Auth0.

A basic Home page displaying authenticated user info.


A Python backend API that:

Receives the Auth0 credentials/token from the frontend.

Verifies the token.

Uses AWS Cognito, configured to use the same Auth0 application (OIDC), and calls Cognito with AWS access/secret key + session token.


Everything runs locally via Docker/Docker Compose, while Auth0 + Cognito are "real" cloud services.


The goal is portfolio-quality: clean structure, clear configuration, minimal but realistic.

> Treat this as if you are implementing it to showcase your experience with authentication integrations in interviews.




---

1. High-level Architecture

Auth Flow (happy path):

1. User opens React app at http://localhost:<frontend-port>.


2. User clicks Login.


3. React app uses Auth0 SPA flow (Universal Login or hosted login) to authenticate the user.


4. Auth0 issues an ID token / access token (JWT).


5. React app stores the token (in memory or secure storage) and:

Shows a Home page with user profile info (from the token).

Sends the token to the backend in API calls (e.g. Authorization: Bearer <access_token>).



6. Python backend:

Validates the incoming Auth0 JWT (issuer, audience, signature, expiry).

Uses AWS SDK with AWS access key, secret key, and optional session token from environment variables.

Calls AWS Cognito (User Pool or Identity Pool), which is pre-configured to use Auth0 as an OIDC IdP using the same Auth0 application.

Returns a simple JSON response (e.g. “Hello, <user>, Cognito call OK”).




Important constraints:

Local only:

Frontend and backend run as Docker containers on the developer machine.

Auth0 and AWS Cognito are real services configured in their dashboards.


No secrets in repo. Use environment variables and .env files referenced in Docker.



---

2. Repo Structure

Implement as a single repository:

root/
  frontend/          # React app
  backend/           # Python API
  docker-compose.yml
  README.md
  .env               # root-level (optional) – do not commit
  .gitignore


---

3. Global Configuration & Environment

3.1. Required Environment Variables

Define the following (exact names can be adjusted but must be consistent and documented):

Auth0:

AUTH0_DOMAIN

AUTH0_CLIENT_ID

AUTH0_CLIENT_SECRET (if needed for backend / machine-to-machine)

AUTH0_AUDIENCE (API identifier configured in Auth0)


AWS / Cognito:

AWS_ACCESS_KEY_ID

AWS_SECRET_ACCESS_KEY

AWS_SESSION_TOKEN (optional, if using temporary credentials)

AWS_REGION

COGNITO_USER_POOL_ID or COGNITO_IDENTITY_POOL_ID (depending on chosen integration)

COGNITO_CLIENT_ID (for the app in Cognito, if used)

COGNITO_AUTH0_PROVIDER_NAME (e.g. the OIDC IdP name configured in Cognito that represents Auth0)


Runtime:

BACKEND_PORT (e.g. 8000)

FRONTEND_PORT (e.g. 3000)

BACKEND_BASE_URL (e.g. http://backend:8000 inside Docker, http://localhost:8000 outside)


> To do

[ ] Add .env.example with all env var names and short descriptions.

[ ] Add .gitignore entries for .env, node_modules, Python venv, build folders.





---

4. Backend (Python) – Detailed Requirements

Choose a simple framework such as FastAPI or Flask. Use whichever is more comfortable, but ensure:

Clear routing.

Easy JWT validation.

Minimal dependencies.


4.1. Backend Goals

Expose a health check endpoint (no auth).

Expose a protected endpoint that:

Requires a valid Auth0 JWT (sent by frontend).

Verifies the JWT.

Uses AWS SDK to call Cognito (e.g. simple “describe” or “get” call).

Returns a JSON payload to the frontend including:

Authenticated user identifier from the JWT (e.g. sub, email).

A small subset of information returned by Cognito (or at least confirmation that Cognito call succeeded).




4.2. Backend API Design

Endpoints:

1. GET /health

Purpose: Liveness check.

Auth: None.

Response: { "status": "ok" }.



2. GET /me

Purpose: Demo authenticated endpoint.

Auth: Requires Auth0 JWT.

Input:

Authorization: Bearer <access_token> header sent by frontend.


Backend logic (pseudocode-style):

token = extract_bearer_token(request.headers["Authorization"])
jwt_payload = validate_jwt_with_auth0(token)

user_id = jwt_payload["sub"]
user_email = jwt_payload.get("email")

# Call Cognito using AWS SDK
cognito_result = call_cognito_with_aws_credentials(user_id, jwt_payload)

return {
  "auth0_user": {
    "sub": user_id,
    "email": user_email,
    # optionally more claims
  },
  "cognito_result": cognito_result_minimal_summary
}

Error handling:

Invalid/missing token → 401 Unauthorized with simple JSON.

AWS/Cognito error → 502 Bad Gateway or 500 with minimal error info.





4.3. JWT Validation Requirements

Use Auth0’s JWKS to verify signature.

Validate:

iss matches https://<AUTH0_DOMAIN>/.

aud matches AUTH0_AUDIENCE (or AUTH0_CLIENT_ID, depending on the flow).

exp not expired.


Cache JWKS keys to avoid fetching for every request.


> To do

[ ] Configure a small JWT validation helper/module.

[ ] Add unit tests (or at least basic tests) for the validator using a mocked token.




4.4. Cognito Integration

Use AWS SDK for Python (boto3).

Load AWS credentials from environment variables.


High-level options (choose one and implement):

1. Cognito User Pool + Auth0 as OIDC IdP

Cognito is configured to accept Auth0 tokens as an external IdP (using the same Auth0 app).

Backend scenario: use Cognito admin APIs to fetch some user-related data based on a mapping from Auth0 sub to Cognito user attributes.



2. Cognito Identity Pool using Auth0 as IdP

Backend scenario: use the Auth0 token to obtain temporary AWS credentials or validate mapping.




For this POC, keep the code extremely simple:

Implement a function like:

def call_cognito_with_aws_credentials(user_id, jwt_payload):
    # Example: describe some Cognito resource or list attributes
    client = boto3.client("cognito-idp", region_name=AWS_REGION)
    # Choose a simple, non-destructive call:
    response = client.describe_user_pool(UserPoolId=COGNITO_USER_POOL_ID)
    return {
        "user_pool_id": response["UserPool"]["Id"],
        "name": response["UserPool"]["Name"]
    }

The focus is showing authenticated AWS access using AWS credentials, not implementing a full user management layer.


> To do

[ ] Implement call_cognito_with_aws_credentials.

[ ] Handle AWS errors gracefully and map them to clean HTTP responses.




4.5. Backend Dockerization

Create backend/Dockerfile that:

Uses a small Python base image.

Copies requirements.txt and installs dependencies.

Copies source code.

Exposes BACKEND_PORT.

Uses a clear CMD to run the app (e.g. uvicorn main:app --host 0.0.0.0 --port 8000 for FastAPI).


The backend must read configuration from environment variables (passed from docker-compose.yml).


> To do

[ ] Add Dockerfile for backend.

[ ] Verify containerization: app responds correctly to /health.




4.6. Backend Acceptance Criteria

[ ] GET /health returns {"status":"ok"} without authentication.

[ ] GET /me without Authorization header returns 401.

[ ] GET /me with a valid Auth0 access token:

[ ] JWT is validated.

[ ] call_cognito_with_aws_credentials is executed using AWS credentials from env.

[ ] JSON response includes:

[ ] Auth0 user sub and (if available) email.

[ ] A field showing Cognito call succeeded (e.g. user pool name or a flag).



[ ] Running backend via Docker (with correct env vars) works locally.



---

5. Frontend (React) – Detailed Requirements

Use a minimal React app, either plain React + Vite/CRA or similar. No need for heavy state management; keep it simple and focused on auth flow.

5.1. Frontend Goals

Two main views:

Login Page

Home Page (Protected)


Use Auth0 SPA SDK (or React SDK) to:

Redirect to Auth0 for login.

Handle callback.

Obtain ID / access tokens.


Send the access token to backend as a Bearer token.


5.2. UI Requirements

Pages / Routes:

1. / – Login/Welcome page

Shows:

App name (e.g. “Auth0 + Cognito POC”).

A short description of the POC.

A “Login with Auth0” button.


If already authenticated, redirects to /home.



2. /home – Protected Home page

Only accessible if the user is authenticated with Auth0.

Displays:

Basic user profile: name, email, Auth0 sub.

A button “Call Protected Backend /me”.


On click:

Calls backend /me with Authorization: Bearer <access_token>.

Displays JSON response in a simple preformatted block.




3. /callback – optional explicit route if needed:

Handles Auth0 redirect callback (depending on library).




Components:

AuthProvider wrapper for providing Auth0 context (if using Auth0 React SDK).

Reusable ProtectedRoute or equivalent to guard /home.


> To do

[ ] Setup routing (e.g. react-router-dom).

[ ] Implement guarded route for /home.




5.3. Auth0 Integration in Frontend

Configure Auth0 client using environment variables (via build-time env, e.g. VITE_ or REACT_APP_):

VITE_AUTH0_DOMAIN

VITE_AUTH0_CLIENT_ID

VITE_AUTH0_AUDIENCE

VITE_AUTH0_REDIRECT_URI (e.g. http://localhost:<frontend-port>/callback)


Initialization (pseudocode):

<Auth0Provider
  domain={AUTH0_DOMAIN}
  clientId={AUTH0_CLIENT_ID}
  authorizationParams={{
    redirect_uri: VITE_AUTH0_REDIRECT_URI,
    audience: VITE_AUTH0_AUDIENCE
  }}
>
  <App />
</Auth0Provider>

When calling backend /me:

const token = await getAccessTokenSilently();
fetch(`${BACKEND_BASE_URL}/me`, {
  headers: { Authorization: `Bearer ${token}` }
});


> To do

[ ] Display clear login/logout buttons and the current auth state.

[ ] Ensure logout works (clear Auth0 session and app state).




5.4. Frontend Dockerization

Create frontend/Dockerfile that:

Uses Node base image.

Installs dependencies.

Builds the app.

Serves the built static files via a simple HTTP server (like nginx or Node's serve), or runs dev server for POC (document which).


Environment variables for Auth0 and backend URL must be available at build time or runtime, depending on chosen approach.

The frontend must be able to call backend via the Docker network (e.g. backend service name backend in docker-compose).


> To do

[ ] Add Dockerfile for frontend.

[ ] Confirm frontend can reach backend /health and /me from inside Docker.




5.5. Frontend Acceptance Criteria

[ ] Visiting / shows a login button when not authenticated.

[ ] Clicking Login redirects to Auth0 and then back to the app.

[ ] After login, /home shows:

[ ] User’s Auth0 sub and email.

[ ] A button to call backend /me.


[ ] Clicking “Call Protected Backend” displays JSON response from backend.

[ ] Logging out returns user to an unauthenticated state, and /home becomes inaccessible.



---

6. Docker Compose & Local Run

Create docker-compose.yml in repo root:

Services:

frontend

Build from ./frontend.

Ports: "3000:3000" (or chosen FRONTEND_PORT).

Environment:

Auth0 env vars (frontend-specific).

VITE_BACKEND_BASE_URL pointing to http://backend:<BACKEND_PORT>.



backend

Build from ./backend.

Ports: "8000:8000" (or chosen BACKEND_PORT).

Environment:

Auth0 env vars.

AWS credentials.

Cognito identifiers.

Any framework-specific settings.





> To do

[ ] Implement docker-compose.yml wiring frontend and backend together.

[ ] Document single command to start everything (e.g. docker-compose up --build).





---

7. Documentation (README)

Create a concise but clear README.md that:

1. Explains the purpose:

POC showcasing Auth0 + AWS Cognito + local Dockerized React/Python stack.



2. Lists prerequisites:

Docker

Docker Compose

Auth0 tenant & application

AWS account with Cognito configured to use Auth0 as OIDC IdP (same Auth0 app).



3. Setup Steps (step-by-step):

Clone repo.

Copy .env.example to .env and fill in real Auth0/AWS values.

Run docker-compose up --build.

Open browser at http://localhost:<FRONTEND_PORT>.



4. Auth Flow Description:

Short section describing the end-to-end flow: user → Auth0 → React → Python → Cognito.



5. Security Notes:

Emphasize that it’s a POC; no secrets should ever be committed.

Note that cookies/local storage vs in-memory token handling is simplified for demo purposes.




> To do

[ ] Add a small architecture diagram (ASCII or image) if desired, or just textual sequence steps.

[ ] Highlight how this repo demonstrates knowledge of Auth0, Cognito, JWT, and Docker.





---

8. Prompt-Style Guidance (for AI or future self)

If this ticket is used as a prompt for another assistant or as a self-reminder, prepend something like:
