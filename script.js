document.addEventListener("DOMContentLoaded", () => {
    const productList = document.querySelector(".product_list");
    const searchInput = document.getElementById("search");
    const filterButton = document.querySelector("button");

    let products = [];

    async function fetchProducts() {
        try {
            const response = await fetch("http://127.0.0.1:5000/products");
            const newProducts = await response.json();

            // Only update if there are changes
          //  if (JSON.stringify(products) !== JSON.stringify(newProducts)) {
            products = newProducts;
            renderProducts();
            //}
        } catch (error) {
            console.error("Error fetching products:", error);
        }
    }

    function renderProducts(filteredProducts = products) {
        productList.innerHTML = "";
        filteredProducts.forEach(product => {
            const glowDiv = document.createElement("div");
            glowDiv.classList.add("glowing-effect");

            const productDiv = document.createElement("div");
            productDiv.classList.add("product");
            productDiv.innerHTML = `
                <img src="${product.image}" alt="${product.name}" class="img_product">
                <h3>${product.name}</h3>MMM
                <p>Price: $${product.price}</p>
            `;

            const button = document.createElement("button");
            button.classList.add("button-85");
            button.textContent = "Add to cart";
            button.addEventListener("click", () => addToCart(product.id));

            productDiv.appendChild(button);
            glowDiv.appendChild(productDiv);
            productList.appendChild(glowDiv);
        });
    }

    function filterProducts() {
        const searchTerm = searchInput.value.toLowerCase();
        const filtered = products.filter(product => 
            product.name.toLowerCase().includes(searchTerm)
        );
        renderProducts(filtered);
    }

    function addToCart(productId) {
        alert(`Product ${productId} added to cart!`);
    }

    searchInput.addEventListener("input", filterProducts);
    
    if (filterButton) {
        filterButton.addEventListener("click", filterProducts);
    }

    fetchProducts();
    setInterval(fetchProducts, 10000); // Refresh product list every 10 seconds
});
