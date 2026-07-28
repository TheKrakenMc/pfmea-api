-- Migration reverted because created_at is a partition key and cannot be altered directly.
-- The timezone issue is handled in Python code instead.
SELECT 1;
