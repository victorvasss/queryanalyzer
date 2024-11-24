-- Таблица клиентов
CREATE TABLE Customers (
    customer_id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    email VARCHAR(100) UNIQUE NOT NULL,
    phone VARCHAR(15)
);

-- Таблица категорий
CREATE TABLE Categories (
    category_id SERIAL PRIMARY KEY,
    name VARCHAR(50) NOT NULL
);

-- Таблица товаров
CREATE TABLE Products (
    product_id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    description TEXT,
    price NUMERIC(10, 2) NOT NULL,
    category_id INT,
    FOREIGN KEY (category_id) REFERENCES Categories(category_id)
);

-- Таблица заказов
CREATE TABLE Orders (
    order_id SERIAL PRIMARY KEY,
    customer_id INT NOT NULL,
    order_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    status VARCHAR(50) DEFAULT 'Pending',
    FOREIGN KEY (customer_id) REFERENCES Customers(customer_id)
);

-- Таблица товаров в заказе
CREATE TABLE OrderItems (
    order_item_id SERIAL PRIMARY KEY,
    order_id INT NOT NULL,
    product_id INT NOT NULL,
    quantity INT NOT NULL CHECK (quantity > 0),
    price NUMERIC(10, 2) NOT NULL,
    FOREIGN KEY (order_id) REFERENCES Orders(order_id),
    FOREIGN KEY (product_id) REFERENCES Products(product_id)
);

-- Пример заполнения категорий
-- INSERT INTO Categories (name) VALUES ('Electronics'), ('Books'), ('Clothing'), ('Home'), ('Beauty');

-- -- Пример заполнения товаров
-- INSERT INTO Products (name, description, price, category_id)
-- VALUES
--     ('Smartphone', 'High-end smartphone with 128GB storage', 599.99, 1),
--     ('Laptop', '15-inch laptop with 16GB RAM', 1099.99, 1),
--     ('Book - Novel', 'A bestselling novel', 14.99, 2),
--     ('T-shirt', 'Comfortable cotton t-shirt', 19.99, 3),
--     ('Blender', 'Powerful blender for smoothies', 89.99, 4);