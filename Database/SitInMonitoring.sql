CREATE DATABASE SitInMonitoring;

USE SitInMonitoring;

CREATE TABLE Users (
    id INT IDENTITY(1,1) PRIMARY KEY,
    username VARCHAR(50) UNIQUE NOT NULL,
    password VARCHAR(255) NOT NULL,
    email VARCHAR(100) UNIQUE NOT NULL,
    lastname VARCHAR(50) NOT NULL,
    firstname VARCHAR(50) NOT NULL,
    middlename VARCHAR(50) NULL,
    course VARCHAR(50) NOT NULL,
    yearlevel VARCHAR(20) NOT NULL
);
Select * from Users;