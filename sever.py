from flask import Flask, jsonify

app = Flask(__name__)

# Sample product data
products = [
    {"id": 1, "name": "Product 1", "price": 100, "image": "static/images/1.jpg"},
    {"id": 2, "name": "Product 2", "price": 200, "image": "static/images/2.jpg"},
    {"id": 3, "name": "Product 3", "price": 300, "image": "static/images/3.jpg"},
    {"id": 4, "name": "Product 4", "price": 400, "image": "static/images/4.jpg"},
    {"id": 5, "name": "Product 5", "price": 500, "image": "static/images/5.jpg"},
    {"id": 6, "name": "Product 6", "price": 600, "image": "static/images/6.jpg"},
{"id": 7, "name": "Product 7", "price": 600, "image": "static/images/2.jpg"},
{"id": 8, "name": "Product 7", "price": 600, "image": "static/images/4.jpg"}]

@app.route("/products", methods=["GET"])
def get_products():
    return jsonify(products)

if __name__ == "__main__":
    app.run(debug=True)
