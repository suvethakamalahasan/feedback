-- =====================================================================
-- Ice Cream Shop Customer Feedback System
-- Sample Data Script
-- =====================================================================
-- Populates the feedback table with realistic sample records so the
-- frontend and admin dashboard can be tested immediately.
--
-- Usage (MySQL CLI):
--   mysql -u root -p icecream_feedback_db < sample_data.sql
-- =====================================================================

USE icecream_feedback_db;

INSERT INTO feedback
    (customer_name, email, phone, visit_date, flavour,
     taste_rating, quality_rating, staff_rating, cleanliness_rating, overall_rating,
     visit_again, recommend_shop, comments, image_path, created_at)
VALUES
('Aarav Sharma', 'aarav.sharma@example.com', '9876543210', '2026-07-01', 'Chocolate Fudge',
 5, 5, 4, 5, 5, 'Yes', 'Yes', 'Best chocolate ice cream I have ever had! Loved the ambience too.', NULL, '2026-07-01 14:32:00'),

('Priya Nair', 'priya.nair@example.com', '9123456780', '2026-07-02', 'Strawberry Swirl',
 4, 4, 5, 4, 4, 'Yes', 'Yes', 'Great service, the staff was very friendly and attentive.', NULL, '2026-07-02 16:10:00'),

('Rohit Verma', 'rohit.verma@example.com', '9988776655', '2026-07-03', 'Mango Delight',
 3, 3, 3, 3, 3, 'No', 'No', 'It was okay, nothing special. Store was a bit crowded.', NULL, '2026-07-03 12:45:00'),

('Sneha Iyer', 'sneha.iyer@example.com', '9765432109', '2026-07-04', 'Vanilla Bean',
 5, 4, 5, 5, 5, 'Yes', 'Yes', 'Absolutely loved the vanilla bean flavor, very authentic taste.', NULL, '2026-07-04 18:20:00'),

('Karan Mehta', 'karan.mehta@example.com', '9871234560', '2026-07-05', 'Butterscotch',
 4, 5, 4, 4, 4, 'Yes', 'Yes', 'Butterscotch was crunchy and delicious. Will visit again for sure.', NULL, '2026-07-05 15:05:00'),

('Ananya Das', 'ananya.das@example.com', '9012345678', '2026-07-06', 'Cookies and Cream',
 2, 3, 2, 3, 2, 'No', 'No', 'Service was slow and the ice cream had melted a bit before serving.', NULL, '2026-07-06 11:15:00'),

('Vikram Singh', 'vikram.singh@example.com', '9345678901', '2026-07-07', 'Pistachio',
 5, 5, 5, 5, 5, 'Yes', 'Yes', 'Outstanding! Every single scoop was perfect. Highly recommend the pistachio.', NULL, '2026-07-07 19:00:00'),

('Meera Pillai', 'meera.pillai@example.com', '9456123789', '2026-07-08', 'Black Currant',
 4, 4, 4, 5, 4, 'Yes', 'Yes', 'Lovely tangy flavor, clean seating area, will come back with family.', NULL, '2026-07-08 13:40:00'),

('Arjun Reddy', 'arjun.reddy@example.com', '9567891234', '2026-07-09', 'Mint Chocolate Chip',
 3, 4, 3, 4, 3, 'Yes', 'No', 'Good flavor but a bit pricey compared to other shops nearby.', NULL, '2026-07-09 17:25:00'),

('Ishita Kapoor', 'ishita.kapoor@example.com', '9678912345', '2026-07-10', 'Chocolate Fudge',
 5, 5, 5, 4, 5, 'Yes', 'Yes', 'Second time here and it did not disappoint. Consistent quality every time.', NULL, '2026-07-10 20:10:00');
