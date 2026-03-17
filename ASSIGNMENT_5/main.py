from fastapi import FastAPI, Query

app = FastAPI()

# -------------------------------
# Sample Data
# -------------------------------

products = [
    {"id": 1, "name": "Wireless Mouse", "price": 499, "category": "Electronics"},
    {"id": 2, "name": "Notebook", "price": 99, "category": "Stationery"},
    {"id": 3, "name": "USB Hub", "price": 799, "category": "Electronics"},
    {"id": 4, "name": "Pen Set", "price": 49, "category": "Stationery"},
]

orders = []


# ---
# Q1
# ---
@app.get("/products/search")
def search_products(keyword: str):
    result = [
        p for p in products
        if keyword.lower() in p["name"].lower()
    ]

    if not result:
        return {
            "message": f"No products found for keyword: {keyword}"
        }

    return {
        "keyword": keyword,
        "total_found": len(result),
        "products": result
    }


# ---
# Q2
# ---
@app.get("/products/sort")
def sort_products(
    sort_by: str = "price",
    order: str = "asc"
):
    if sort_by not in ["price", "name"]:
        return {"error": "sort_by must be 'price' or 'name'"}

    if order not in ["asc", "desc"]:
        return {"error": "order must be 'asc' or 'desc'"}

    sorted_products = sorted(
        products,
        key=lambda p: p[sort_by],
        reverse=(order == "desc")
    )

    return {
        "sort_by": sort_by,
        "order": order,
        "products": sorted_products
    }


# ---
# Q3
# ---
@app.get("/products/page")
def paginate_products(
    page: int = 1,
    limit: int = 2
):
    start = (page - 1) * limit
    end = start + limit

    total = len(products)
    total_pages = -(-total // limit)

    return {
        "page": page,
        "limit": limit,
        "total_products": total,
        "total_pages": total_pages,
        "products": products[start:end]
    }

# -------------------
# Create Order for q4
# -------------------
@app.post("/orders")
def create_order(customer_name: str, product_id: int, quantity: int):
    product = next((p for p in products if p["id"] == product_id), None)

    if not product:
        return {"message": "Product not found"}

    order = {
        "order_id": len(orders) + 1,
        "customer_name": customer_name,
        "product_id": product_id,
        "product_name": product["name"],
        "quantity": quantity,
        "total_price": product["price"] * quantity
    }

    orders.append(order)
    return {
        "message": "Order created successfully",
        "order": order
    }


# ---
# Q4
# ---
@app.get("/orders/search")
def search_orders(customer_name: str = Query(...)):
    result = [
        o for o in orders
        if customer_name.lower() in o["customer_name"].lower()
    ]

    if not result:
        return {"message": f"No orders found for: {customer_name}"}

    return {
        "customer_name": customer_name,
        "total_found": len(result),
        "orders": result
    }


# ---
# Q5
# ---
@app.get("/products/sort-by-category")
def sort_by_category():
    result = sorted(products, key=lambda p: (p["category"], p["price"]))

    return {
        "products": result,
        "total": len(result)
    }


# ---
# Q6
# ---
@app.get("/products/browse")
def browse_products(
    keyword: str = None,
    sort_by: str = "price",
    order: str = "asc",
    page: int = 1,
    limit: int = 4
):
    result = products

    # Search
    if keyword:
        result = [
            p for p in result
            if keyword.lower() in p["name"].lower()
        ]

    # Validation
    if sort_by not in ["price", "name"]:
        return {"error": "sort_by must be 'price' or 'name'"}

    if order not in ["asc", "desc"]:
        return {"error": "order must be 'asc' or 'desc'"}

    # Sort
    result = sorted(
        result,
        key=lambda p: p[sort_by],
        reverse=(order == "desc")
    )

    # Pagination
    total = len(result)
    total_pages = -(-total // limit) if total > 0 else 0

    start = (page - 1) * limit
    paged = result[start:start + limit]

    return {
        "keyword": keyword,
        "sort_by": sort_by,
        "order": order,
        "page": page,
        "limit": limit,
        "total_found": total,
        "total_pages": total_pages,
        "products": paged
    }

# -------------------------------
# Existing Product by ID
# -------------------------------
@app.get("/products/{product_id}")
def get_product(product_id: int):
    for product in products:
        if product["id"] == product_id:
            return product

    return {"message": "Product not found"}
