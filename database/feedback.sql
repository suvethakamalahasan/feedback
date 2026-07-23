-- =====================================================================
-- Ice Cream Shop Customer Feedback System
-- Database Schema Script
-- =====================================================================
-- This script creates the database and the feedback table used by the
-- FastAPI backend. Run this once before starting the backend server.
--
-- Usage (MySQL CLI):
--   mysql -u root -p < feedback.sql
-- =====================================================================

-- ---------------------------------------------------------------------
-- 1. Create Database
-- ---------------------------------------------------------------------
CREATE DATABASE IF NOT EXISTS icecream_feedback_db
    CHARACTER SET utf8mb4
    COLLATE utf8mb4_unicode_ci;

USE icecream_feedback_db;

-- ---------------------------------------------------------------------
-- 2. Drop table if it already exists (safe re-run for development)
-- ---------------------------------------------------------------------
DROP TABLE IF EXISTS feedback;

-- ---------------------------------------------------------------------
-- 3. Create feedback table
-- ---------------------------------------------------------------------
CREATE TABLE feedback (
    id                  INT AUTO_INCREMENT PRIMARY KEY,

    -- Customer information
    customer_name       VARCHAR(150)        NOT NULL,
    email               VARCHAR(150)        NOT NULL,
    phone               VARCHAR(20)         NOT NULL,
    visit_date          DATE                NOT NULL,

    -- Visit details
    flavour             VARCHAR(100)        NOT NULL,

    -- Ratings (1 to 5)
    taste_rating         TINYINT UNSIGNED    NOT NULL,
    quality_rating        TINYINT UNSIGNED    NOT NULL,
    staff_rating          TINYINT UNSIGNED    NOT NULL,
    cleanliness_rating    TINYINT UNSIGNED    NOT NULL,
    overall_rating        TINYINT UNSIGNED    NOT NULL,

    -- Yes/No feedback
    visit_again          ENUM('Yes', 'No')   NOT NULL,
    recommend_shop        ENUM('Yes', 'No')   NOT NULL,

    -- Free text
    comments             TEXT                NULL,

    -- Optional uploaded image path (relative to backend/uploads)
    image_path           VARCHAR(255)        NULL,

    -- Audit column
    created_at           TIMESTAMP           NOT NULL DEFAULT CURRENT_TIMESTAMP,

    -- Data integrity constraints for rating columns (1-5 only)
    CONSTRAINT chk_taste_rating       CHECK (taste_rating BETWEEN 1 AND 5),
    CONSTRAINT chk_quality_rating     CHECK (quality_rating BETWEEN 1 AND 5),
    CONSTRAINT chk_staff_rating       CHECK (staff_rating BETWEEN 1 AND 5),
    CONSTRAINT chk_cleanliness_rating CHECK (cleanliness_rating BETWEEN 1 AND 5),
    CONSTRAINT chk_overall_rating     CHECK (overall_rating BETWEEN 1 AND 5)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ---------------------------------------------------------------------
-- 4. Helpful indexes for the admin dashboard (search / filter / sort)
-- ---------------------------------------------------------------------
CREATE INDEX idx_feedback_visit_date     ON feedback (visit_date);
CREATE INDEX idx_feedback_overall_rating ON feedback (overall_rating);
CREATE INDEX idx_feedback_email          ON feedback (email);
CREATE INDEX idx_feedback_customer_name  ON feedback (customer_name);
CREATE INDEX idx_feedback_created_at     ON feedback (created_at);
