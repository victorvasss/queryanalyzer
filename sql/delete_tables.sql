-- Удаление таблицы товаров в заказе (OrderItems), так как она зависит от Orders и Products
DROP TABLE IF EXISTS OrderItems;

-- Удаление таблицы заказов (Orders), так как она зависит от таблицы Customers
DROP TABLE IF EXISTS Orders;

-- Удаление таблицы товаров (Products), так как она зависит от Categories
DROP TABLE IF EXISTS Products;

-- Удаление таблицы категорий (Categories)
DROP TABLE IF EXISTS Categories;

-- Удаление таблицы клиентов (Customers)
DROP TABLE IF EXISTS Customers;