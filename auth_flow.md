# JWT Authentication Flow

User
↓
Signup API
POST /api/signup/
↓
User Created
↓
Login API
POST /api/login/
↓
JWT Tokens Generated
↓
Access Token
+
Refresh Token
↓
User Stores Access Token
↓
Bearer Authentication
Authorization:
Bearer ACCESS_TOKEN
↓
Protected API Access
↓
Permission Checking
(IsAuthenticated)
↓
Role Checking
(IsAdmin / IsEmployer / IsCandidate)
↓
Access Granted
OR
Access Denied


# Authentication Workflow Explanation

1. User registers using the signup API.

2. User logs in using the login API.

3. The server generates:

   * Access Token
   * Refresh Token

4. The client stores the access token.

5. The client sends:

Authorization:
Bearer ACCESS_TOKEN

with every protected API request.

6. Django REST Framework validates:

* Token validity
* Token expiry
* User authentication
* User permissions

7. If validation succeeds:

Access Granted

8. If validation fails:

Access Denied
