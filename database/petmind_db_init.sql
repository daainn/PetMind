create database petminddb;
use petminddb;

CREATE TABLE dogs_breed (
    breed_id INT PRIMARY KEY,
    name VARCHAR(100),
    image_url VARCHAR(255),
    description TEXT
);

CREATE TABLE users (
    user_id CHAR(36) PRIMARY KEY,
    email VARCHAR(100),
    password VARCHAR(100),
    is_verified BOOLEAN,
    created_at DATETIME,
    is_deleted BOOLEAN,
    deleted_at DATETIME
);

CREATE TABLE dogs_profile (
    dog_id INT PRIMARY KEY,
    breed_id INT NOT NULL,
    user_id CHAR(36) NOT NULL,
    name VARCHAR(100),
    breed_name VARCHAR(100),
    age INT,
    gender ENUM('남아', '여아'),
    neutered ENUM('완료','미완료','모름'),
    medical_history TEXT,
    living_period ENUM('1년 미만', '1년 이상 ~ 3년 미만', '3년 이상 ~ 10년 미만', '10년 이상'),
    residence_type ENUM('아파트','단독주택','빌라/다세대','기타'),
    image_url VARCHAR(255),
    created_at DATETIME,
    updated_at DATETIME
);

CREATE TABLE chats (
    chat_id INT PRIMARY KEY,
    dog_id INT NOT NULL,
    title TEXT,
    created_at DATETIME
);

CREATE TABLE messages (
    message_id INT PRIMARY KEY,
    chat_id INT,
    sender ENUM('user', 'bot'),
    body TEXT,
    created_at DATETIME
);

CREATE TABLE contents (
    content_id INT PRIMARY KEY,
    title VARCHAR(200),
    body TEXT,
    image_url VARCHAR(255),
    created_at DATETIME,
    updated_at DATETIME,
    source_url VARCHAR(200)
);

CREATE TABLE content_recommendations (
    content_id INT,
    chat_id INT,
    PRIMARY KEY (content_id, chat_id),
    FOREIGN KEY (content_id) REFERENCES contents(content_id),
    FOREIGN KEY (chat_id) REFERENCES chats(chat_id)
);

CREATE TABLE user_review (
    review_id INT PRIMARY KEY,
    chat_id INT,
    rating INT,
    review TEXT,
    created_at DATETIME
);


