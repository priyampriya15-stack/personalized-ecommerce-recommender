# REST API Documentation — Personalized E-Commerce Recommendation Engine

This document provides exhaustive documentation for all REST API endpoints implemented in Phase 4.

**Base URL**: `http://localhost:5000`  
**API Prefix**: `/api`  
**Authentication Standard**: RFC 7519 JSON Web Tokens (JWT) passed via `Authorization: Bearer <token>` header.

---

## Standard Response Schemas

### Standard Success Structure
```json
{
  "success": true,
  "data": { ... },
  "message": "Operation completed successfully."
}
```

### Standard Error Structure
```json
{
  "success": false,
  "error": {
    "code": "ERROR_CODE",
    "message": "Human-readable description of what went wrong."
  }
}
```

---

## 1. Authentication APIs

### 1.1 User Registration
- **Method**: `POST`
- **URL**: `/api/auth/register`
- **Auth Required**: None (Public)
- **Request Body**:
```json
{
  "name": "Jane Doe",
  "email": "jane.doe@example.com",
  "password": "SecurePassword123!",
  "categories": ["All Beauty", "Digital Music"]  // optional onboarding preferences
}
```
- **Validation**:
  - `name`: String, minimum 2 characters.
  - `email`: Valid RFC 5322 format, unique constraint enforced.
  - `password`: String, minimum 8 characters.
- **Success Response (201 Created)**:
```json
{
  "success": true,
  "data": {
    "user": {
      "id": 5,
      "name": "Jane Doe",
      "email": "jane.doe@example.com",
      "role": "user",
      "created_at": "2026-10-20T17:40:00.000Z"
    },
    "token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
  },
  "message": "Registration successful."
}
```
- **Error Cases**:
  - `400 Bad Request`: Invalid email format or password length < 8 (`INVALID_INPUT`).
  - `409 Conflict`: Email already registered (`EMAIL_EXISTS`).

---

### 1.2 User Login
- **Method**: `POST`
- **URL**: `/api/auth/login`
- **Auth Required**: None (Public)
- **Request Body**:
```json
{
  "email": "jane.doe@example.com",
  "password": "SecurePassword123!"
}
```
- **Success Response (200 OK)**:
```json
{
  "success": true,
  "data": {
    "user": {
      "id": 5,
      "name": "Jane Doe",
      "email": "jane.doe@example.com",
      "role": "user",
      "created_at": "2026-10-20T17:40:00.000Z"
    },
    "token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
  },
  "message": "Login successful."
}
```
- **Error Cases**:
  - `400 Bad Request`: Email or password omitted (`MISSING_CREDENTIALS`).
  - `401 Unauthorized`: Invalid email or incorrect password (`INVALID_CREDENTIALS`).

---

### 1.3 Get Current User Profile
- **Method**: `GET`
- **URL**: `/api/auth/me`
- **Auth Required**: Yes (`Bearer <token>`)
- **Success Response (200 OK)**:
```json
{
  "success": true,
  "data": {
    "id": 5,
    "name": "Jane Doe",
    "email": "jane.doe@example.com",
    "role": "user",
    "created_at": "2026-10-20T17:40:00.000Z",
    "preferred_categories": ["All Beauty"],
    "cart_items_count": 2
  },
  "message": "User profile retrieved."
}
```
- **Error Cases**:
  - `401 Unauthorized`: Token missing, expired, or invalid (`UNAUTHORIZED`).

---

## 2. Product APIs

### 2.1 List Products
- **Method**: `GET`
- **URL**: `/api/products`
- **Auth Required**: None (Public)
- **Query Parameters**:
  - `page` (int, default 1)
  - `limit` (int, default 20, max 100)
  - `category` (string, e.g. `All_Beauty`)
  - `min_price` (float)
  - `max_price` (float)
  - `min_rating` (float)
  - `sort` (`price_asc` | `price_desc` | `rating_asc` | `rating_desc` | `title_asc`, default `rating_desc`)
- **Success Response (200 OK)**:
```json
{
  "success": true,
  "data": {
    "products": [
      {
        "id": 32,
        "external_product_id": "B0BTLTVR1X",
        "title": "Zydeco Chop Chop Cajun Seasoning Base...",
        "description": "Premium dehydrated seasoning blend...",
        "category": "All Beauty",
        "price": 17.49,
        "rating": 5.0,
        "image_url": "https://m.media-amazon.com/images/I/51hGpA1YYEL.jpg"
      }
    ],
    "total": 1499,
    "page": 1,
    "total_pages": 75,
    "limit": 20
  },
  "message": "Products retrieved."
}
```

---

### 2.2 Get Product Details
- **Method**: `GET`
- **URL**: `/api/products/<product_identifier>`
- **Auth Required**: None (Public)
- **Identifier**: Database integer `id` (e.g. `32`) or Amazon ASIN `external_product_id` (e.g. `B0BTLTVR1X`).
- **Success Response (200 OK)**:
```json
{
  "success": true,
  "data": {
    "id": 32,
    "external_product_id": "B0BTLTVR1X",
    "title": "Zydeco Chop Chop Cajun Seasoning Base...",
    "description": "Premium dehydrated seasoning blend...",
    "category": "All Beauty",
    "price": 17.49,
    "rating": 5.0,
    "image_url": "https://m.media-amazon.com/images/I/51hGpA1YYEL.jpg"
  },
  "message": "Product retrieved."
}
```
- **Error Cases**:
  - `404 Not Found`: Product ID or ASIN does not exist (`NOT_FOUND`).

---

### 2.3 Search Products
- **Method**: `GET`
- **URL**: `/api/products/search`
- **Auth Required**: None (Public)
- **Query Parameters**:
  - `q` (string, required): Search query matching title, description, or category.
  - `page` (int, default 1)
  - `limit` (int, default 20)
- **Success Response (200 OK)**:
```json
{
  "success": true,
  "data": {
    "products": [ ... ],
    "total": 17,
    "page": 1,
    "total_pages": 1,
    "limit": 20
  },
  "message": "Found 17 products."
}
```
- **Error Cases**:
  - `400 Bad Request`: Query parameter `q` is missing (`MISSING_QUERY`).

---

### 2.4 List Categories
- **Method**: `GET`
- **URL**: `/api/products/categories`
- **Auth Required**: None (Public)
- **Success Response (200 OK)**:
```json
{
  "success": true,
  "data": [
    {"name": "All Beauty", "count": 1499},
    {"name": "Appliances", "count": 3393},
    {"name": "Digital Music", "count": 3445}
  ],
  "message": "Categories retrieved."
}
```

---

### 2.5 Get Similar Products
- **Method**: `GET`
- **URL**: `/api/products/<product_identifier>/similar`
- **Auth Required**: None (Public)
- **Engine**: Content-Based Filtering using TF-IDF feature vectors and Cosine Similarity.
- **Query Parameters**:
  - `limit` (int, default 6, max 20)
- **Success Response (200 OK)**:
```json
{
  "success": true,
  "data": [
    {
      "rank": 1,
      "product_id": "B011M4J8W2",
      "title": "CHOP MALL Crystal Rhinestone Yellow...",
      "category": "All Beauty",
      "price": 12.99,
      "rating": 4.8,
      "image_url": "https://m.media-amazon.com/...",
      "score": 0.1977,
      "algorithm": "content_based",
      "explanation": "Shares characteristics and category with Zydeco Chop Chop..."
    }
  ],
  "message": "Similar products retrieved."
}
```

---

## 3. Recommendation APIs

### 3.1 Popularity Recommendations
- **Method**: `GET`
- **URL**: `/api/recommendations/popular`
- **Auth Required**: None (Public / Cold Guests)
- **Algorithm**: Bayesian Weighted Rating: $WR = \frac{v}{v+m} R + \frac{m}{v+m} C$
- **Query Parameters**:
  - `limit` (int, default 10, max 30)
  - `category` (string, optional category filter)
- **Success Response (200 OK)**:
```json
{
  "success": true,
  "data": [
    {
      "rank": 1,
      "product_id": "B011G0V050",
      "title": "Victory",
      "category": "Digital Music",
      "price": 10.99,
      "rating": 5.0,
      "image_url": "https://m.media-amazon.com/...",
      "score": 4.9622,
      "algorithm": "popularity",
      "explanation": "Top-rated in Digital Music with 33 customer reviews"
    }
  ],
  "message": "Popular recommendations retrieved."
}
```

---

### 3.2 Personalized Hybrid Recommendations
- **Method**: `GET`
- **URL**: `/api/recommendations/<user_id>` OR `/api/recommendations/<user_id>/hybrid`
- **Auth Required**: Yes (`Bearer <token>`)
- **Security**: Caller can only request recommendations for their own `user_id` unless role is `admin`.
- **Formula**: $\text{Hybrid Score} = \alpha \cdot \text{CF\_Score} + (1 - \alpha) \cdot \text{CB\_Score}$
- **Query Parameters**:
  - `limit` (int, default 10, max 30)
  - `alpha` (float, range `[0.0, 1.0]`, optional override)
- **Success Response (200 OK)**:
```json
{
  "success": true,
  "data": [
    {
      "rank": 1,
      "product_id": "B002K88N22",
      "title": "Palmers Olive Oil Formula Hand Cream With Vit-E 2.1 Ounce",
      "category": "All Beauty",
      "price": 6.84,
      "rating": 4.7,
      "image_url": "https://m.media-amazon.com/...",
      "score": 0.2920,
      "algorithm": "hybrid",
      "explanation": "Matches items in your browsing and rating history"
    }
  ],
  "message": "Personalized hybrid recommendations retrieved."
}
```
- **Error Cases**:
  - `401 Unauthorized`: Token missing or expired (`UNAUTHORIZED`).
  - `403 Forbidden`: Attempting to query another user's recommendations (`FORBIDDEN`).

---

### 3.3 Collaborative Filtering Recommendations
- **Method**: `GET`
- **URL**: `/api/recommendations/<user_id>/collaborative`
- **Auth Required**: Yes (`Bearer <token>`)
- **Algorithm**: Truncated SVD Matrix Factorization ($k=30$ latent factors). Automatically applies Bayesian popularity fallback for cold users.
- **Success Response (200 OK)**:
```json
{
  "success": true,
  "data": [
    {
      "rank": 1,
      "product_id": "B011G0V050",
      "title": "Victory",
      "category": "Digital Music",
      "price": 10.99,
      "rating": 5.0,
      "image_url": "https://m.media-amazon.com/...",
      "score": 4.9622,
      "algorithm": "popularity",
      "explanation": "Top-rated in Digital Music with 33 customer reviews"
    }
  ],
  "message": "Collaborative recommendations retrieved."
}
```

---

### 3.4 Content-Based Filtering Recommendations
- **Method**: `GET`
- **URL**: `/api/recommendations/<user_id>/content-based`
- **Auth Required**: Yes (`Bearer <token>`)
- **Algorithm**: Weighted user profile vector constructed from interaction history and category preferences matched against TF-IDF item vectors.
- **Success Response (200 OK)**:
```json
{
  "success": true,
  "data": [
    {
      "rank": 1,
      "product_id": "B002K88N22",
      "title": "Palmers Olive Oil Formula Hand Cream With Vit-E 2.1 Ounce",
      "category": "All Beauty",
      "price": 6.84,
      "rating": 4.7,
      "image_url": "https://m.media-amazon.com/...",
      "score": 0.2728,
      "algorithm": "content_based",
      "explanation": "Matches your browsing history and category preferences"
    }
  ],
  "message": "Content-based recommendations retrieved."
}
```

---

## 4. Interaction APIs

### 4.1 Record User Interaction
- **Method**: `POST`
- **URL**: `/api/interactions`
- **Auth Required**: Yes (`Bearer <token>`)
- **Request Body**:
```json
{
  "product_id": 32,                    // integer product ID or external ASIN string
  "interaction_type": "rating",        // 'view' | 'like' | 'rating' | 'cart' | 'purchase'
  "rating": 5.0                        // float between 1.0 and 5.0 (required for 'rating')
}
```
- **Success Response (201 Created)**:
```json
{
  "success": true,
  "data": {
    "id": 21,
    "user_id": 4,
    "product_id": 32,
    "product_title": "Zydeco Chop Chop Cajun Seasoning Base...",
    "external_product_id": "B0BTLTVR1X",
    "category": "All Beauty",
    "image_url": "https://m.media-amazon.com/images/I/51hGpA1YYEL.jpg",
    "price": 17.49,
    "interaction_type": "rating",
    "rating": 5.0,
    "timestamp": "2026-10-20T17:44:49.938Z"
  },
  "message": "Interaction recorded successfully."
}
```
- **Error Cases**:
  - `400 Bad Request`: Invalid type or rating outside `[1.0, 5.0]` (`INVALID_RATING` or `INVALID_TYPE`).
  - `404 Not Found`: Product not found in database (`NOT_FOUND`).

---

### 4.2 Get User Interaction History
- **Method**: `GET`
- **URL**: `/api/users/<user_id>/history`
- **Auth Required**: Yes (`Bearer <token>`)
- **Query Parameters**:
  - `type` (string, optional: `view` | `like` | `rating` | `cart` | `purchase`)
  - `limit` (int, default 50, max 100)
- **Success Response (200 OK)**:
```json
{
  "success": true,
  "data": [
    {
      "id": 21,
      "user_id": 4,
      "product_id": 32,
      "product_title": "Zydeco Chop Chop Cajun Seasoning Base...",
      "external_product_id": "B0BTLTVR1X",
      "category": "All Beauty",
      "interaction_type": "rating",
      "rating": 5.0,
      "timestamp": "2026-10-20T17:44:49.938Z"
    }
  ],
  "message": "User history retrieved."
}
```

---

### 4.3 Update User Preferences
- **Method**: `POST`
- **URL**: `/api/users/preferences`
- **Auth Required**: Yes (`Bearer <token>`)
- **Request Body**:
```json
{
  "categories": ["All Beauty", "Appliances"]
}
```
- **Success Response (200 OK)**:
```json
{
  "success": true,
  "data": {
    "preferred_categories": ["All Beauty", "Appliances"]
  },
  "message": "Preferences updated successfully."
}
```

---

## 5. Shopping Cart APIs

### 5.1 View Cart
- **Method**: `GET`
- **URL**: `/api/cart`
- **Auth Required**: Yes (`Bearer <token>`)
- **Success Response (200 OK)**:
```json
{
  "success": true,
  "data": {
    "id": 4,
    "user_id": 4,
    "items": [
      {
        "id": 1,
        "product_id": 32,
        "product": {
          "id": 32,
          "title": "Zydeco Chop Chop...",
          "price": 17.49,
          "image_url": "https://..."
        },
        "quantity": 2,
        "subtotal": 34.98
      }
    ],
    "total_price": 34.98,
    "total_items": 2
  },
  "message": "Cart retrieved."
}
```

---

### 5.2 Add / Update Cart Item
- **Method**: `POST`
- **URL**: `/api/cart/items`
- **Auth Required**: Yes (`Bearer <token>`)
- **Request Body**:
```json
{
  "product_id": 32,
  "quantity": 1
}
```
- **Success Response (200 OK)**:
```json
{
  "success": true,
  "data": {
    "item": {
      "product_id": 32,
      "quantity": 1,
      "subtotal": 17.49
    },
    "total_items": 1,
    "total_price": 17.49
  },
  "message": "Cart updated."
}
```

---

### 5.3 Remove Cart Item
- **Method**: `DELETE`
- **URL**: `/api/cart/items/<product_identifier>`
- **Auth Required**: Yes (`Bearer <token>`)
- **Success Response (200 OK)**:
```json
{
  "success": true,
  "data": { "removed_product_id": 32 },
  "message": "Item removed from cart."
}
```

---

### 5.4 Cart Checkout
- **Method**: `POST`
- **URL**: `/api/cart/checkout`
- **Auth Required**: Yes (`Bearer <token>`)
- **Description**: Real purchase transaction. Records `purchase` interaction records in the database, audits purchase telemetry, and clears active cart.
- **Success Response (200 OK)**:
```json
{
  "success": true,
  "data": {
    "purchased_items_count": 1,
    "total_amount": 17.49
  },
  "message": "Checkout completed successfully."
}
```

---

## 6. Admin APIs

### 6.1 Platform Analytics
- **Method**: `GET`
- **URL**: `/api/admin/analytics`
- **Auth Required**: Yes (`Bearer <admin_token>`)
- **Role Required**: `admin`
- **Success Response (200 OK)**:
```json
{
  "success": true,
  "data": {
    "overview": {
      "total_users": 4,
      "total_products": 8337,
      "total_interactions": 22,
      "total_recommendation_calls": 5,
      "current_hybrid_alpha": 0.25
    },
    "interaction_breakdown": {
      "like": 1,
      "rating": 21
    },
    "category_statistics": {
      "All Beauty": 1499,
      "Appliances": 3393,
      "Digital Music": 3445
    },
    "algorithm_usage": {
      "hybrid": 4,
      "popularity": 1
    },
    "recent_interactions": [ ... ]
  },
  "message": "Platform analytics retrieved."
}
```
- **Error Cases**:
  - `401 Unauthorized`: Token missing or invalid (`UNAUTHORIZED`).
  - `403 Forbidden`: Authenticated user role is not `admin` (`FORBIDDEN`).

---

### 6.2 Offline Evaluation Model Metrics
- **Method**: `GET`
- **URL**: `/api/admin/model-metrics`
- **Auth Required**: Yes (`Bearer <admin_token>`)
- **Role Required**: `admin`
- **Success Response (200 OK)**:
```json
{
  "success": true,
  "data": {
    "model_comparison": [
      {
        "Model": "Hybrid (alpha=0.25)",
        "K": 10,
        "Precision@K": 0.0215,
        "Recall@K": 0.2100,
        "F1@K": 0.0389,
        "NDCG@K": 0.14199,
        "MAP@K": 0.1102,
        "Coverage@K (%)": 34.50,
        "Diversity@K": 0.7012
      }
    ],
    "alpha_experiments": [ ... ]
  },
  "message": "Model metrics retrieved."
}
```

---

### 6.3 Update Recommendation Settings
- **Method**: `PUT`
- **URL**: `/api/admin/recommendation-settings`
- **Auth Required**: Yes (`Bearer <admin_token>`)
- **Role Required**: `admin`
- **Request Body**:
```json
{
  "alpha": 0.35
}
```
- **Validation**: `alpha` must be float between `0.0` and `1.0` inclusive.
- **Success Response (200 OK)**:
```json
{
  "success": true,
  "data": {
    "current_hybrid_alpha": 0.35,
    "collaborative_weight": 0.35,
    "content_weight": 0.65
  },
  "message": "Hybrid alpha successfully updated to 0.35."
}
```
- **Error Cases**:
  - `400 Bad Request`: `alpha` missing or out of `[0.0, 1.0]` bounds (`INVALID_ALPHA`).
  - `403 Forbidden`: Non-admin caller (`FORBIDDEN`).
