# E-Commerce Order Management System

Scalable backend api to handle product sales using pessimistic locking to unsure data consistency. this project is my solution for chronicles backend intern technical test.

## Prerequisites

- **Docker/Podman**
- **Docker Compose/Podman Compose**

## Quick Start with Docker

### 1. Clone the Repository

```bash
git clone https://github.com/Cakra17/Technical-Test
cd Technical-Test
```

### 2. Start All Services

```bash
# Build and start all services
docker compose up -d --build
# if using podman
podman compose up -d --build
```

This will start:

- **PostgreSQL** on port `5432`
- **Redis** on port `6379`
- **FastAPI API** on port `8000`
- **Celery Worker** (background processing)

### 3. Access the Application

- **API Base URL**: <http://localhost:8000/api/v1>
- **API Documentation (Swagger)**: <http://localhost:8000/docs>
- **Health Check**: <http://localhost:8000/api/v1/health>

### 4. Stop Services

```bash
# Stop all services
docker compose down
# if using podman
podman compose down
```

### 5. Running Test

```bash
# Running pytest
pytest -vv

```

## API Documentation

### Interactive API Documentation

Once the application is running, visit:

- **Swagger UI**: <http://localhost:8000/docs>

### API Endpoints

#### Products

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/v1/products` | Create a new product |
| GET | `/api/v1/products` | Get all products (paginated) |
| GET | `/api/v1/products/{productId}` | Get product by ID |
| PUT | `/api/v1/products/{productId}` | Update product |
| DELETE | `/api/v1/products/{productId}` | Delete product |

#### Orders

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/v1/orders` | Create a new order (async processing) |
| GET | `/api/v1/orders` | Get all orders (paginated) |
| GET | `/api/v1/orders/{orderId}` | Get order by ID |

### Example Requests

<details>
<summary><b>Create Product</b></summary>

```bash
curl -X POST "http://localhost:8000/api/v1/products" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Gaming Laptop",
    "price": 1299,
    "stock": 50
  }'
```

Response:

```json
{
  "message": "Product created successfully",
  "data": {
    "id": "123e4567-e89b-12d3-a456-426614174000",
    "name": "Gaming Laptop",
    "price": 1299,
    "stock": 50,
    "created_at": "2025-01-08T10:00:00Z"
  }
}
```

</details>

<details>
<summary><b>Create Order</b></summary>

```bash
curl -X POST "http://localhost:8000/api/v1/orders" \
  -H "Content-Type: application/json" \
  -d '{
    "product_id": "123e4567-e89b-12d3-a456-426614174000",
    "amount": 3
  }'
```

Response:

```json
{
  "message": "Order created and queued for processing",
  "order_id": "987fcdeb-51a2-43f7-8c9d-3b2a1e5f6789",
}
```

</details>

<details>
<summary><b>Check Order Status</b></summary>

```bash
curl "http://localhost:8000/api/v1/orders/987fcdeb-51a2-43f7-8c9d-3b2a1e5f6789"
```

Response (Success):

```json
{
  "data": {
    "id": "987fcdeb-51a2-43f7-8c9d-3b2a1e5f6789",
    "amount": 3,
    "total_price": 3897,
    "status": "success",
    "created_at": "2025-01-08T10:05:00Z"
  }
}
```

Response (Failed - Insufficient Stock):

```json
{
  "data": {
    "id": "987fcdeb-51a2-43f7-8c9d-3b2a1e5f6789",
    "amount": 100,
    "total_price": 129900,
    "status": "failed",
    "created_at": "2025-01-08T10:05:00Z"
  }
}
```

</details>

## Race Condition Handling

### The Problem

In a high-traffic e-commerce system, multiple users might try to purchase the same product simultaneously. Without proper handling, this can lead to **overselling** (selling more items than available in stock).

**Example Scenario Without Protection:**

```
Time    User A              User B              Stock
----    ------              ------              -----
T1      Check stock: 1      -                   1
T2      -                   Check stock: 1      1
T3      Both see stock!     Both see stock!     1
T4      Buy 1 item          Buy 1 item          1
T5      Stock = 0           Stock = -1         -1 (OVERSOLD!)
```

### Solution: Two-Phase Processing with Database Locking

 I'm implement a **background validation approach** with PostgreSQL row-level locking to prevent race conditions:

#### Phase 1: Fast Order Creation

```python
async def AddOrder(order: OrderPayload):
    # Quick insert without stock validation
    # Order status: "pending"
    # Returns immediately to user
```

#### Phase 2: Background Validation (Celery Worker)

```python
async def validateOrder(orderId: str):
    async with conn.transaction():
        # 1. Lock order row using FOR UPDATE
        await cur.execute("""
            SELECT id, product_id, amount, total_price, status FROM orders WHERE id = %s FOR UPDATE
        """, (order_id,))

        # check if order is exist
        order = await cur.fetchone()
          if not order:
            # raise error

        # check if order status is pending
        if order[4] != "pending":
            # raise eror
        
        # 2. Lock product row
        await cur.execute("""
            SELECT status FROM orders 
            WHERE id = %s 
            FOR UPDATE
        """, (orderId,))
        
        # 3. Check stock availability
        if amount > stock:
            # Update order status to "failed"
            # Don't raise exception - commit the status update
            return {"status": "failed"}
        
        # 4. Deduct stock and confirm order
        await cur.execute("""
            UPDATE products SET stock = stock - %s WHERE id = %s
        """, (amount, product_id))
        
        await cur.execute("""
            UPDATE orders SET status = 'success' WHERE id = %s
        """, (orderId,))
        
        # Transaction commits - all changes saved together
```

### How It Prevents Race Conditions

**With Protection (FOR UPDATE lock):**

```
Time    User A Order          User B Order          Stock
----    --------------        --------------        -----
T1      Create (pending)                            10
T2                            Create (pending)      10
T3      [Worker A] LOCK row                         10
T4                            [Worker B] WAITING... 10
T5      Check: 10 >= 5                              10
T6      Deduct: stock = 5                           5
T7      COMMIT & UNLOCK                             5
T8                            [LOCK acquired]       5
T9                            Check: 5 >= 8         5
T10                           Status = failed       5
T11                           COMMIT                5
```

### Key Techniques Used

1. **`FOR UPDATE` Row Locking**
   - Locks the product row until transaction completes
   - Other transactions must wait for the lock to be released
   - Ensures only one worker processes a product at a time

2. **Consistent Lock Order**
   - Always lock products before orders
   - Prevents deadlocks when multiple orders use the same product

3. **Transactional Updates**
   - Stock deduction and order confirmation happen atomically
   - Either both succeed or both fail - no partial updates

4. **Asynchronous Processing**
   - API responds immediately (status: "pending")
   - Heavy validation happens in background
   - User doesn't wait for stock checking

5. **Status-Based State Management**

   ```
   pending → (validation) → success/failed
   ```

### Testing Race Conditions

You can test the race condition prevention by creating multiple concurrent orders:

```bash
# Create 10 orders simultaneously for product with stock of 5
for i in {1..10}; do
  curl -X POST "http://localhost:8000/api/v1/orders" \
    -H "Content-Type: application/json" \
    -d '{"product_id": "<product-id>", "amount": 1}' &
done
wait

# Result: Only 5 orders will succeed, 5 will fail
# No overselling will occur!
```
