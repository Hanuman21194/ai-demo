from fastapi import FastAPI
from fast_api_models import Product
app = FastAPI()
@app.get("/")
def greet():
    return "Welcme to first api app build"
products=[
   Product(id=1,name="apple",description="costly phone",price=99,quantity=10),
   Product(id=3,name="samsung",description="budget phone",price=89,quantity=12)
]
@app.get("/products")
def get_all_products():
    return products

@app.get("/products/{id}")
def product_by_id(id:int):
    for product in products:
        if product.id ==id:
            return product
    return "product not found"    


@app.post("/products/")
def add_product(product:Product):
    products.append(product)
    return products

