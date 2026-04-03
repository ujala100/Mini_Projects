-- 1. Database
CREATE DATABASE IF NOT EXISTS courier_system_v3;
USE courier_system_v3;

-- 2. Tables
CREATE TABLE users (
    user_id INT PRIMARY KEY AUTO_INCREMENT,
    name VARCHAR(50),
    email VARCHAR(59),
    role ENUM('customer','franchise','admin')
); 

CREATE TABLE franchise (
    franchise_id INT PRIMARY KEY AUTO_INCREMENT,
    name VARCHAR(50),
    city VARCHAR(59),
    commission_percent DECIMAL(5,2)
); 

CREATE TABLE courier (
    courier_id INT PRIMARY KEY AUTO_INCREMENT,
    customer_id INT,
    franchise_id INT,
    weight DECIMAL(5,2),
    distance DECIMAL(6,2),
    price DECIMAL(8,2),
    status VARCHAR(30),
    booking_date DATE,
    FOREIGN KEY (customer_id) REFERENCES users(user_id),
    FOREIGN KEY (franchise_id) REFERENCES franchise(franchise_id)
);

CREATE TABLE revenue (
    revenue_id INT PRIMARY KEY AUTO_INCREMENT,
    courier_id INT,
    franchise_earning DECIMAL(8,2),
    admin_earning DECIMAL(8,2),
    FOREIGN KEY (courier_id) REFERENCES courier(courier_id)
); 

-- 3. Insert sample data
INSERT INTO users (name,email,role) VALUES
('aditya','fgfhg@gmvh.bjy','admin'),
('ghjhjb','hgjhbkl@gmvh.bjy','customer'),
('hjgo','khju@gmvh.bjy','franchise'),
('blh','g@gmvh.bjy','admin'),
('aaaaa','jjjj@gmvh.bjy','customer');

INSERT INTO franchise (name,city,commission_percent) VALUES
('aditya','f',20),
('ghjhjb','hg',10),
('hjgo','kh',5),
('blh','g',15),
('aaaaa','j',5);

-- 4. Trigger to calculate revenue automatically
DELIMITER $$

CREATE TRIGGER after_courier_insert
AFTER INSERT ON courier
FOR EACH ROW
BEGIN
    DECLARE f_share DECIMAL(8,2);
    DECLARE a_share DECIMAL(8,2);
    DECLARE commission DECIMAL(5,2);
    DECLARE price DECIMAL(8,2);

    -- get commission & price
    SELECT commission_percent, NEW.price INTO commission, price
    FROM franchise
    WHERE franchise_id = NEW.franchise_id;

    SET f_share = price * commission / 100;
    SET a_share = price - f_share;

    -- insert into revenue
    INSERT INTO revenue (courier_id, franchise_earning, admin_earning)
    VALUES (NEW.courier_id, f_share, a_share);
END$$

DELIMITER ;

-- 5. Insert courier data (revenue will auto-calculate)
INSERT INTO courier (customer_id, franchise_id, weight, distance, price, status, booking_date) VALUES
(1,2,100,2500,12000,'booked',CURDATE()),
(3,1,500,2500,200,'not_booked',CURDATE()),
(2,4,900,2500,1500,'not_booked',CURDATE()),
(4,3,700,2500,3000,'booked',CURDATE()),
(5,5,50,2500,20000,'booked',CURDATE());

-- 6. Check revenue table
SELECT * FROM revenue;

-- 7. Create a view for franchise revenue
CREATE OR REPLACE VIEW franchise_revenue AS
SELECT 
    f.name AS franchise_name,
    SUM(r.franchise_earning) AS total
FROM revenue r
JOIN courier c ON r.courier_id = c.courier_id
JOIN franchise f ON c.franchise_id = f.franchise_id
GROUP BY f.name;

-- 8. Query the view
SELECT * FROM franchise_revenue
ORDER BY total DESC;

-- 9. Monthly revenue report
SELECT MONTH(booking_date) AS month, SUM(price) AS total_price
FROM courier
GROUP BY MONTH(booking_date);

-- 10. Index on booking_date
CREATE INDEX idx_date ON courier(booking_date);