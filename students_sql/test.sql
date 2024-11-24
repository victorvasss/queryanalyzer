SELECT * FROM Categories;
SELECT name FROM Products WHERE price > 100;
SELECT name FROM Products WHERE category_id IS NOT NULL ORDER BY price DESC LIMIT 3;
SELECT category_id, AVG(price) AS avg_price FROM Products GROUP BY category_id;