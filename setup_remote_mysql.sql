-- MySQL setup commands for remote server 118.139.176.89
-- Run these commands on your remote MySQL server
-- Create the database
CREATE DATABASE IF NOT EXISTS taiwanewshorts CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
-- Create the user for any host (%)
CREATE USER IF NOT EXISTS 'admin_tw'@'%' IDENTIFIED BY '10Hn1a0!407';
-- Grant all privileges on the taiwanewshorts database
GRANT ALL PRIVILEGES ON taiwanewshorts.* TO 'admin_tw'@'%';
-- Also grant specific permissions
GRANT SELECT, INSERT, UPDATE, DELETE, CREATE, DROP, INDEX, ALTER ON taiwanewshorts.* TO 'admin_tw'@'%';
-- Apply the changes
FLUSH PRIVILEGES;
-- Show the user was created
SELECT User, Host FROM mysql.user WHERE User = 'admin_tw';
-- Show databases to confirm taiwanewshorts exists
SHOW DATABASES;
