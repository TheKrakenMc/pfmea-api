-- Make the 'code' column optional in the 'technologies' table
ALTER TABLE technologies ALTER COLUMN code DROP NOT NULL;
