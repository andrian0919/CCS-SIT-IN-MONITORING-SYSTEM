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
    yearlevel VARCHAR(20) NOT NULL,
    role VARCHAR(20) NOT NULL DEFAULT 'student'
);

CREATE TABLE Sessions (
    id INT IDENTITY(1,1) PRIMARY KEY,
    user_id INT NOT NULL,
    remaining_sessions INT NOT NULL DEFAULT 10,
    FOREIGN KEY (user_id) REFERENCES Users(id) ON DELETE CASCADE
);

CREATE TABLE Reservation (
    id INT IDENTITY(1,1) PRIMARY KEY,
    student_id VARCHAR(50) NOT NULL,
    lastname VARCHAR(50) NOT NULL,
    firstname VARCHAR(50) NOT NULL,
    date DATE NOT NULL,
    time TIME NOT NULL,
    purpose VARCHAR(100) NOT NULL,
    lab VARCHAR(50) NOT NULL,
    available_pc VARCHAR(50) NOT NULL,
    FOREIGN KEY (student_id) REFERENCES Users(student_id) ON DELETE CASCADE
);


CREATE TABLE Labs (
    id INT PRIMARY KEY IDENTITY(1,1),
    lab_name NVARCHAR(50) NOT NULL
);

CREATE TABLE PCs (
    id INT PRIMARY KEY IDENTITY(1,1),
    lab_id INT NOT NULL,
    pc_name NVARCHAR(50) NOT NULL,
    is_available BIT NOT NULL DEFAULT 1,
    FOREIGN KEY (lab_id) REFERENCES Labs(id)
);

INSERT INTO Users (student_id, password, email, lastname, firstname, course, yearlevel, role)
VALUES 
    ('admin', 'admin123', 'admin@example.com', 'Admin', 'User', 'N/A', 'N/A', 'admin'),
    ('staff', 'staff123', 'staff@example.com', 'Staff', 'User', 'N/A', 'N/A', 'staff');

INSERT INTO PCs (lab_id, pc_name, is_available) 
VALUES 
((SELECT id FROM Labs WHERE lab_name = '524'), 'PC 1', 1),
((SELECT id FROM Labs WHERE lab_name = '524'), 'PC 2', 1),
((SELECT id FROM Labs WHERE lab_name = '526'), 'PC 3', 1),
((SELECT id FROM Labs WHERE lab_name = '526'), 'PC 4', 1),
((SELECT id FROM Labs WHERE lab_name = '530'), 'PC 5', 1),
((SELECT id FROM Labs WHERE lab_name = '544'), 'PC 6', 1),
((SELECT id FROM Labs WHERE lab_name = '542'), 'PC 7', 1);



Select * from Reservation;