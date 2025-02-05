CREATE DATABASE SitInMonitoring;

USE SitInMonitoring;

CREATE TABLE Users (
    id INT IDENTITY(1,1) PRIMARY KEY,
    student_id VARCHAR(50) UNIQUE NOT NULL,
    password VARCHAR(255) NOT NULL,
    email VARCHAR(100) UNIQUE NOT NULL,
    lastname VARCHAR(50) NOT NULL,
    firstname VARCHAR(50) NOT NULL,
    middlename VARCHAR(50) NULL,
    course VARCHAR(50) NOT NULL,
    yearlevel VARCHAR(20) NOT NULL
);

CREATE TABLE Sessions (
    id INT IDENTITY(1,1) PRIMARY KEY,
    user_id INT NOT NULL,
    remaining_sessions INT NOT NULL DEFAULT 10,
    FOREIGN KEY (user_id) REFERENCES Users(id) ON DELETE CASCADE
);

CREATE TABLE Reservations (
    id INT IDENTITY(1,1) PRIMARY KEY,
    student_id INT NOT NULL,
    date VARCHAR(20) NOT NULL,
    time VARCHAR(20) NOT NULL,
    FOREIGN KEY (student_id) REFERENCES Users(id) ON DELETE CASCADE
);

Select * from Users;