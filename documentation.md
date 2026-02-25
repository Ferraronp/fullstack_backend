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
| Model            | Table            | Fields                                                                                                                                      |
|------------------|------------------|---------------------------------------------------------------------------------------------------------------------------------------------|
| **User**         | `users`          | `id: int PK`, `email: str unique`, `hashed_password: str`, `currency: str default "$"`, `role: str default "user"`                          |
| **Category**     | `categories`     | `id: int PK`, `name: str unique`, `color: str nullable`, `user_id: int FK -> users.id`                                                      |
| **Operation**    | `operations`     | `id: int PK`, `date: date`, `amount: float`, `comment: str nullable`, `category_id: int FK -> categories.id`, `user_id: int FK -> users.id` |
| **RevokedToken** | `revoked_tokens` | `id: int PK`, `token: str unique`, `created_at: datetime`                                                                                   |

## Pydantic Schemas (`schemas/`)
### `user.py`
- **UserBase** – `email: EmailStr`
- **UserCreate** – `email`, `password`, `currency` (default "$"), `role` (default "user").
- **UserOut** – `id`, `email`, `currency`, `role`.
- **RoleUpdate** – `role: str`.

### `auth.py`
- **Token** – `access_token`, `token_type`.
- **TokenData** – `user_id: Optional[int]`.

### `category.py`
- **CategoryBase** – `name`, `color` (optional).
- **CategoryCreate** – наследует от CategoryBase.
- **Category** – `id`, `name`, `color`.

### `operation.py`
- **OperationBase** – `date`, `amount`, `comment`, `category_id` (optional).
- **OperationCreate** – наследует от OperationBase.
- **Operation** – `id`, `date`, `amount`, `comment`, `category_id`, `category` (optional).

## Authentication (`utils/auth.py`)
- **create_access_token(data: dict, expires_delta: Optional[timedelta] = None)** – generates a JWT.
- **get_current_user(token: str = Depends(oauth2_scheme))** – validates token and returns the `User` model.

## Role Management (`utils/role.py`)
Utility functions to check user roles and enforce permissions in routers.

## Routers and Endpoints
All routers are included in `main.py`.

### 1. `routers/users.py` (префикс `/auth`)
| Method | Path             | Description              | Request Body | Response        | Auth         |
|--------|------------------|--------------------------|--------------|-----------------|--------------|
| `POST` | `/auth/register` | Register a new user      | `UserCreate` | `UserOut` (200) | None         |
| `POST` | `/auth/login`    | Obtain JWT token         | `UserCreate` | `Token` (200)   | None         |
| `GET`  | `/auth/me`       | Get current user profile | –            | `UserOut` (200) | Bearer token |
| `POST` | `/auth/logout`   | Logout user              | –            | `None` (200)    | Bearer       |

### 2. `routers/categories.py` (префикс `/categories`)
| Method   | Path                        | Description            | Request Body     | Response               | Auth   |
|----------|-----------------------------|------------------------|------------------|------------------------|--------|
| `GET`    | `/categories/`              | List user's categories | –                | List[`Category`] (200) | Bearer |
| `GET`    | `/categories/{category_id}` | Get specific category  | –                | `Category` (200)       | Bearer |
| `POST`   | `/categories/`              | Create a category      | `CategoryCreate` | `Category` (200)       | Bearer |
| `PUT`    | `/categories/{category_id}` | Update category        | `CategoryCreate` | `Category` (200)       | Owner  |
| `DELETE` | `/categories/{category_id}` | Delete category        | –                | `None` (200)           | Owner  |

### 3. `routers/operations.py` (префикс `/operations`)
| Method   | Path                         | Description                      | Request Body                          | Response                                    | Auth   |
|----------|------------------------------|----------------------------------|---------------------------------------|---------------------------------------------|--------|
| `GET`    | `/operations/`               | List operations (filter by date) | Query params `start_date`, `end_date` | List[`Operation`] (200)                     | Bearer |
| `POST`   | `/operations/`               | Create operation                 | `OperationCreate`                     | `Operation` (200)                           | Bearer |
| `GET`    | `/operations/{operation_id}` | Get operation                    | –                                     | `Operation` (200)                           | Owner  |
| `PUT`    | `/operations/{operation_id}` | Update operation                 | `OperationCreate`                     | `Operation` (200)                           | Owner  |
| `DELETE` | `/operations/{operation_id}` | Delete operation                 | –                                     | `None` (200)                                | Owner  |
| `GET`    | `/operations/balance/total`  | Get total balance                | –                                     | `{"balance": float, "currency": str}` (200) | Bearer |

### 4. `routers/admin.py` (префикс `/admin`)
| Method | Path                          | Description      | Request Body | Response              | Auth       |
|--------|-------------------------------|------------------|--------------|-----------------------|------------|
| `GET`  | `/admin/users`                | List all users   | –            | List[`UserOut`] (200) | Admin only |
| `PUT`  | `/admin/users/{user_id}/role` | Change user role | `RoleUpdate` | `UserOut` (200)       | Admin only |

## Error Handling
- Validation errors return `422 Unprocessable Entity` with details.
- Authentication errors return `401 Unauthorized`.
- Permission errors return `403 Forbidden`.
- Not found resources return `404 Not Found`.
- Email already registered returns `400 Bad Request`.
- Invalid credentials returns `401 Unauthorized`.
- Already logged out returns `200 OK` with appropriate message.

---
*Generated documentation for developers and QA engineers.*