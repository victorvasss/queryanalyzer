-- Пример заполнения категорий
INSERT INTO Categories (name) VALUES ('Electronics'), ('Books'), ('Clothing'), ('Home'), ('Beauty');

-- Пример заполнения товаров
INSERT INTO Products (name, description, price, category_id)
VALUES
    ('Smartphone', 'High-end smartphone with 128GB storage', 599.99, 1),
    ('Laptop', '15-inch laptop with 16GB RAM', 1099.99, 1),
    ('Book - Novel', 'A bestselling novel', 14.99, 2),
    ('T-shirt', 'Comfortable cotton t-shirt', 19.99, 3),
    ('Blender', 'Powerful blender for smoothies', 89.99, 4);