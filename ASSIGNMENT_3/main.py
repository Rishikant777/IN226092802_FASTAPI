from fastapi import FastAPI, HTTPException, Query
from pydantic import BaseModel

app = FastAPI()


# Product model
class Product(BaseModel):
    name: str
    price: int
    category: str
    in_stock: bool


# Initial product list
products = [
    {"id": 1, "name": "Wireless Mouse", "price": 599, "category": "Electronics", "in_stock": True},
    {"id": 2, "name": "Notebook", "price": 99, "category": "Stationery", "in_stock": True},
    {"id": 3, "name": "USB Hub", "price": 799, "category": "Electronics", "in_stock": False},
    {"id": 4, "name": "Pen Set", "price": 49, "category": "Stationery", "in_stock": True}
]


@app.get("/")
def home():
    return {"message": "FastAPI Product API running"}


# Get all products
@app.get("/products")
def get_products():
    return {"products": products}


# Add new product
@app.post("/products")
def add_product(product: Product):
    for p in products:
        if p["name"].lower() == product.name.lower():
            raise HTTPException(status_code=400, detail="Product already exists")

    new_product = {
        "id": len(products) + 1,
        "name": product.name,
        "price": product.price,
        "category": product.category,
        "in_stock": product.in_stock
    }

    products.append(new_product)
    return {"message": "Product added successfully", "product": new_product}


# Discount endpoint
@app.put("/products/discount")
def bulk_discount(
    category: str = Query(...),
    discount_percent: int = Query(..., ge=1, le=99)
):
    updated = []

    for p in products:
        if p["category"].lower() == category.lower():
            p["price"] = int(p["price"] * (1 - discount_percent / 100))
            updated.append(p)

    if not updated:
        return {"message": "No products found in this category"}

    return {
        "message": f"{discount_percent}% discount applied",
        "updated_products": updated
    }


# Audit endpoint
@app.get("/products/audit")
def product_audit():
    in_stock = [p for p in products if p["in_stock"]]
    out_stock = [p for p in products if not p["in_stock"]]

    stock_value = sum(p["price"] * 10 for p in in_stock)
    priciest = max(products, key=lambda x: x["price"])

    return {
        "total_products": len(products),
        "in_stock_count": len(in_stock),
        "out_of_stock_names": [p["name"] for p in out_stock],
        "total_stock_value": stock_value,
        "most_expensive_product": priciest
    }


# Get single product
@app.get("/products/{product_id}")
def get_product(product_id: int):
    for product in products:
        if product["id"] == product_id:
            return product
    raise HTTPException(status_code=404, detail="Product not found")


# Update product
@app.put("/products/{product_id}")
def update_product(product_id: int, price: int = None, in_stock: bool = None):
    for product in products:
        if product["id"] == product_id:

            if price is not None:
                product["price"] = price

            if in_stock is not None:
                product["in_stock"] = in_stock

            return {"message": "Product updated", "product": product}

    raise HTTPException(status_code=404, detail="Product not found")


# Delete product
@app.delete("/products/{product_id}")
def delete_product(product_id: int):
    for index, product in enumerate(products):
        if product["id"] == product_id:
            deleted = products.pop(index)
            return {"message": f"{deleted['name']} deleted"}

    raise HTTPException(status_code=404, detail="Product not found")