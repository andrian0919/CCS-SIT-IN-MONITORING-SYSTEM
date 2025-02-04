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

CREATE TABLE Sessions (
    id INT IDENTITY(1,1) PRIMARY KEY,
    user_id INT FOREIGN KEY REFERENCES Users(id) ON DELETE CASCADE,
    remaining_sessions INT NOT NULL DEFAULT 10 -- Default sessions
);


CREATE TABLE Reservation (
    id INT IDENTITY(1,1) PRIMARY KEY,
    student_id INT NOT NULL,
    date VARCHAR(20) NOT NULL,
    time VARCHAR(20) NOT NULL,
    FOREIGN KEY (student_id) REFERENCES Users(id) ON DELETE CASCADE
);
Select * from Users;

SELECT * FROM Users WHERE student_id IS NULL;

SELECT student_id, COUNT(*) 
FROM Users 
GROUP BY student_id 
HAVING COUNT(*) > 1;

UPDATE Users 
SET student_id = 'TEMP' + CAST(id AS VARCHAR)
WHERE student_id IS NULL;

UPDATE Users
SET student_id = student_id + '_1'
WHERE student_id IN (
    SELECT student_id
    FROM Users
    GROUP BY student_id
    HAVING COUNT(*) > 1
);

ALTER TABLE Users ADD CONSTRAINT UQ_student_id UNIQUE(student_id);

DELETE FROM Sessions WHERE user_id IN (1, 3, 6, 7, 8, 9);
DELETE FROM Reservation WHERE student_id IN (1, 3, 6, 7, 8, 9);
DELETE FROM Users WHERE id IN (1, 3, 6, 7, 8, 9);

