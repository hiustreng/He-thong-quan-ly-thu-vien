CREATE TABLE IF NOT EXISTS books (
    id SERIAL PRIMARY KEY,
    title VARCHAR(255) NOT NULL,
    author VARCHAR(150) NOT NULL,
    quantity INT NOT NULL CHECK (quantity >= 0)
);

CREATE TABLE IF NOT EXISTS readers (
    id SERIAL PRIMARY KEY,
    full_name VARCHAR(150) NOT NULL,
    email VARCHAR(150) UNIQUE NOT NULL
);

CREATE TABLE IF NOT EXISTS borrow_records (
    id SERIAL PRIMARY KEY,
    book_id INT REFERENCES books(id) ON DELETE CASCADE,
    reader_id INT REFERENCES readers(id) ON DELETE CASCADE,
    borrow_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    return_date TIMESTAMP NULL,
    status VARCHAR(20) DEFAULT 'BORROWED'
);

INSERT INTO books (title, author, quantity) VALUES
('Clean Code', 'Robert C. Martin', 5),
('Designing Data-Intensive Applications', 'Martin Kleppmann', 3),
('Docker Deep Dive', 'Nigel Poulton', 4);

INSERT INTO readers (full_name, email) VALUES
('Nguyễn Văn A', 'nguyenvana@example.com'),
('Trần Thị B', 'tranthib@example.com');

CREATE USER app_user WITH PASSWORD 'AppStrongPassword_2026!';
GRANT CONNECT ON DATABASE library_db TO app_user;
GRANT USAGE ON SCHEMA public TO app_user;
GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA public TO app_user;
GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA public TO app_user;
