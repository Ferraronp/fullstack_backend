# Backend Documentation

## Overview
This project is a **Fullstack** application with a FastAPI backend (`fullstack_backend`) and a React frontend (`fullstack_frontend`). The backend provides CRUD operations for users, categories, and financial operations, along with authentication and role‑based access control.

## Getting Started
### Prerequisites
- Python 3.9+
- `pip` installed
- (Optional) Docker for containerised deployment

### Installation
```bash
cd fullstack_backend
pip install -r requirements.txt
```

### Running the Server
```bash
uvicorn main:app --reload
```
The API will be available at `http://127.0.0.1:8000` and the automatic docs at `/docs`.

## Project Structure
```
fullstack_backend/
├─ crud/                # Low‑level database operations
├─ db/                  # Database connection
├─ models/              # SQLAlchemy models
├─ routers/             # FastAPI routers (endpoints)
├─ schemas/             # Pydantic schemas for request/response
├─ utils/               # Helper functions (auth, role, utils)
├─ main.py              # Application entry point
└─ requirements.txt
```

## Database Models (`models/models.py`)
| Model | Table | Fields |
|-------|-------|--------|
| **User** | `users` | `id: int PK`, `username: str`, `email: str`, `hashed_password: str`, `is_active: bool`, `role: str` |
| **Category** | `categories` | `id: int PK`, `name: str`, `description: Optional[str]`, `owner_id: int FK -> users.id` |
| **Operation** | `operations` | `id: int PK`, `amount: float`, `type: str (income/expense)`, `date: datetime`, `category_id: int FK -> categories.id`, `owner_id: int FK -> users.id` |

## Pydantic Schemas (`schemas/`)
### `user.py`
- **UserCreate** – fields: `username`, `email`, `password`.
- **UserRead** – fields: `id`, `username`, `email`, `is_active`, `role`.
- **UserUpdate** – optional fields for updating a user.

### `auth.py`
- **Token** – `access_token`, `token_type`.
- **TokenData** – `username` (optional).

### `category.py`
- **CategoryCreate** – `name`, `description`.
- **CategoryRead** – `id`, `name`, `description`, `owner_id`.
- **CategoryUpdate** – optional `name`, `description`.

### `operation.py`
- **OperationCreate** – `amount`, `type`, `date`, `category_id`.
- **OperationRead** – all fields plus `owner_id`.
- **OperationUpdate** – optional fields for partial update.

## Authentication (`utils/auth.py`)
- **create_access_token(data: dict, expires_delta: Optional[timedelta] = None)** – generates a JWT.
- **get_current_user(token: str = Depends(oauth2_scheme))** – validates token and returns the `User` model.
- **get_current_active_user** – ensures the user is active.
- **get_current_admin_user** – ensures the user has role `admin`.

## Role Management (`utils/role.py`)
Utility functions to check user roles and enforce permissions in routers.

## Routers and Endpoints
All routers are included in `main.py`.

### 1. `routers/users.py` (префикс `/auth`)
| Method | Path | Description | Request Body | Response | Auth |
|--------|------|-------------|--------------|----------|------|
| `POST` | `/auth/register` | Register a new user | `UserCreate` | `UserRead` (201) | None |
| `POST` | `/auth/login` | Obtain JWT token | `OAuth2PasswordRequestForm` | `Token` (200) | None |
| `GET` | `/auth/me` | Get current user profile | – | `UserRead` (200) | Bearer token |
| `POST` | `/auth/logout` | Logout user | – | `{"detail": "Successfully logged out"}` (200) | Bearer |

### 2. `routers/categories.py`
| Method | Path | Description | Request Body | Response | Auth |
|--------|------|-------------|--------------|----------|------|
| `POST` | `/categories/` | Create a category | `CategoryCreate` | `CategoryRead` (201) | Bearer |
| `GET` | `/categories/` | List user's categories | – | List[`CategoryRead`] (200) | Bearer |
| `GET` | `/categories/{id}` | Get specific category | – | `CategoryRead` (200) | Bearer |
| `PUT` | `/categories/{id}` | Update category | `CategoryUpdate` | `CategoryRead` (200) | Owner |
| `DELETE` | `/categories/{id}` | Delete category | – | `{"detail": "Category deleted"}` (200) | Owner |

### 3. `routers/operations.py`
| Method | Path | Description | Request Body | Response | Auth |
|--------|------|-------------|--------------|----------|------|
| `POST` | `/operations/` | Create operation | `OperationCreate` | `OperationRead` (201) | Bearer |
| `GET` | `/operations/` | List operations (filter by date) | Query params `start_date`, `end_date` | List[`OperationRead`] (200) | Bearer |
| `GET` | `/operations/balance/total` | Get total balance | – | `{"total": float}` (200) | Bearer |
| `GET` | `/operations/{id}` | Get operation | – | `OperationRead` (200) | Owner |
| `PUT` | `/operations/{id}` | Update operation | `OperationUpdate` | `OperationRead` (200) | Owner |
| `DELETE` | `/operations/{id}` | Delete operation | – | `{"detail": "Operation deleted"}` (200) | Owner |

### 4. `routers/admin.py`
| Method | Path | Description | Request Body | Response | Auth |
|--------|------|-------------|--------------|----------|------|
| `GET` | `/admin/users` | List all users | – | List[`UserRead`] (200) | Admin only |
| `PUT` | `/admin/users/{user_id}/role` | Change user role | `{"role": "user" or "admin"}` | `UserRead` (200) | Admin only |

## Error Handling
- Validation errors return `422 Unprocessable Entity` with details.
- Authentication errors return `401 Unauthorized`.
- Permission errors return `403 Forbidden`.
- Not found resources return `404 Not Found`.

---
*Generated documentation for developers and QA engineers.*