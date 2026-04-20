-- ANPR Tracking System Database Schema
-- MySQL Database Setup

-- Create Database
CREATE DATABASE IF NOT EXISTS anpr_db;
USE anpr_db;

-- Create Vehicles Table
CREATE TABLE IF NOT EXISTS vehicles (
    id INT AUTO_INCREMENT PRIMARY KEY,
    plate VARCHAR(20) NOT NULL,
    entry_time VARCHAR(20),
    exit_time VARCHAR(20),
    ev_status VARCHAR(10),
    duration VARCHAR(20),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_plate (plate),
    INDEX idx_entry_time (entry_time)
);

-- Insert Sample Data (Optional)
-- INSERT INTO vehicles (plate, entry_time, exit_time, ev_status) 
-- VALUES ('HR98AAQQ00', '01:25:51', '01:26:05', 'NON-EV');
