CREATE DATABASE kintree_db;

CREATE USER kintree_user WITH PASSWORD 'password';

GRANT ALL PRIVILEGES ON DATABASE kintree_db TO kintree_user;

\c kintree_db
GRANT ALL ON SCHEMA public TO kintree_user;
