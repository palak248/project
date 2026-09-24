#!/usr/bin/env bash
set -euo pipefail

DB_NAME="student_performance"
DB_USER="student_performance_app"
DB_PASSWORD="password"
DB_HOST="127.0.0.1"
DB_PORT="3306"

echo "==> Updating package lists..."
sudo apt-get update

echo "==> Installing MySQL server..."
sudo DEBIAN_FRONTEND=noninteractive apt-get install -y \
    mysql-server \
    mysql-client

echo "==> Enabling and starting MySQL..."
sudo systemctl enable mysql
sudo systemctl start mysql

echo "==> Configuring MySQL..."

sudo mysql <<SQL
-- Create the application database
CREATE DATABASE IF NOT EXISTS \`${DB_NAME}\`
    CHARACTER SET utf8mb4
    COLLATE utf8mb4_unicode_ci;

-- Create the application user
CREATE USER IF NOT EXISTS '${DB_USER}'@'${DB_HOST}'
    IDENTIFIED BY '${DB_PASSWORD}';

-- Ensure the password is correct if the user already existed
ALTER USER '${DB_USER}'@'${DB_HOST}'
    IDENTIFIED BY '${DB_PASSWORD}';

-- Grant access only to this application's database
GRANT ALL PRIVILEGES ON \`${DB_NAME}\`.* 
    TO '${DB_USER}'@'${DB_HOST}';

FLUSH PRIVILEGES;
SQL

echo "==> Checking MySQL is listening on port ${DB_PORT}..."
if ! sudo ss -lntp | grep -q ":${DB_PORT} "; then
    echo "WARNING: MySQL is not currently listening on ${DB_PORT}."
    echo "Check: sudo ss -lntp | grep 3306"
fi

echo "==> Testing application database connection..."
MYSQL_PWD="${DB_PASSWORD}" mysql \
    --host="${DB_HOST}" \
    --port="${DB_PORT}" \
    --user="${DB_USER}" \
    --database="${DB_NAME}" \
    -e "SELECT VERSION() AS mysql_version, DATABASE() AS database_name;"

echo
echo "========================================"
echo "MySQL setup completed successfully."
echo "========================================"
echo
echo "Database : ${DB_NAME}"
echo "User     : ${DB_USER}"
echo "Host     : ${DB_HOST}"
echo "Port     : ${DB_PORT}"
echo
echo "Your application configuration:"
echo
echo "FLASK_SECRET_KEY=replace-with-a-local-secret"
echo "MYSQL_HOST=${DB_HOST}"
echo "MYSQL_PORT=${DB_PORT}"
echo "MYSQL_USER=${DB_USER}"
echo "MYSQL_PASSWORD=${DB_PASSWORD}"
echo "MYSQL_DATABASE=${DB_NAME}"
