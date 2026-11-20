-- Salem Makki Portfolio — MySQL schema
-- Generated from app/models.py with `flask export-schema`.
-- Usage:  mysql -u root -p < database/schema.sql

CREATE DATABASE IF NOT EXISTS salem_portfolio
  CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
USE salem_portfolio;
SET NAMES utf8mb4;

CREATE TABLE IF NOT EXISTS admin_users (
	id INTEGER NOT NULL AUTO_INCREMENT, 
	username VARCHAR(64) NOT NULL, 
	password_hash VARCHAR(255) NOT NULL, 
	last_login_at DATETIME, 
	created_at DATETIME NOT NULL, 
	updated_at DATETIME NOT NULL, 
	PRIMARY KEY (id), 
	UNIQUE (username)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;


CREATE TABLE IF NOT EXISTS gallery_images (
	id INTEGER NOT NULL AUTO_INCREMENT, 
	category VARCHAR(20) NOT NULL, 
	path VARCHAR(255) NOT NULL, 
	thumb_path VARCHAR(255) NOT NULL, 
	width INTEGER, 
	height INTEGER, 
	caption_ar VARCHAR(200) NOT NULL, 
	caption_en VARCHAR(200) NOT NULL, 
	is_visible BOOL NOT NULL, 
	sort_order INTEGER NOT NULL, 
	created_at DATETIME NOT NULL, 
	updated_at DATETIME NOT NULL, 
	PRIMARY KEY (id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE INDEX ix_gallery_images_category ON gallery_images (category);

CREATE TABLE IF NOT EXISTS login_attempts (
	id INTEGER NOT NULL AUTO_INCREMENT, 
	ip_address VARCHAR(64) NOT NULL, 
	username VARCHAR(64), 
	success BOOL NOT NULL, 
	created_at DATETIME NOT NULL, 
	PRIMARY KEY (id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE INDEX ix_login_attempts_ip_address ON login_attempts (ip_address);
CREATE INDEX ix_login_attempts_created_at ON login_attempts (created_at);

CREATE TABLE IF NOT EXISTS messages (
	id INTEGER NOT NULL AUTO_INCREMENT, 
	name VARCHAR(120) NOT NULL, 
	email VARCHAR(150) NOT NULL, 
	subject VARCHAR(200) NOT NULL, 
	body TEXT NOT NULL, 
	ip_address VARCHAR(64), 
	is_read BOOL NOT NULL, 
	created_at DATETIME NOT NULL, 
	PRIMARY KEY (id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE INDEX ix_messages_created_at ON messages (created_at);
CREATE INDEX ix_messages_ip_address ON messages (ip_address);
CREATE INDEX ix_messages_is_read ON messages (is_read);

CREATE TABLE IF NOT EXISTS profile (
	id INTEGER NOT NULL AUTO_INCREMENT, 
	full_name_ar VARCHAR(150) NOT NULL, 
	full_name_en VARCHAR(150) NOT NULL, 
	display_name VARCHAR(100) NOT NULL, 
	brand_name VARCHAR(100) NOT NULL, 
	title_ar VARCHAR(150) NOT NULL, 
	title_en VARCHAR(150) NOT NULL, 
	tagline_ar VARCHAR(255) NOT NULL, 
	tagline_en VARCHAR(255) NOT NULL, 
	short_bio_ar TEXT, 
	short_bio_en TEXT, 
	is_available BOOL NOT NULL, 
	availability_ar VARCHAR(120) NOT NULL, 
	availability_en VARCHAR(120) NOT NULL, 
	about_ar TEXT, 
	about_en TEXT, 
	specialization_ar VARCHAR(150) NOT NULL, 
	specialization_en VARCHAR(150) NOT NULL, 
	qualification_ar VARCHAR(200) NOT NULL, 
	qualification_en VARCHAR(200) NOT NULL, 
	interests_ar TEXT, 
	interests_en TEXT, 
	goals_ar TEXT, 
	goals_en TEXT, 
	location_ar VARCHAR(120) NOT NULL, 
	location_en VARCHAR(120) NOT NULL, 
	avatar_path VARCHAR(255), 
	cover_path VARCHAR(255), 
	about_image_path VARCHAR(255), 
	email VARCHAR(150) NOT NULL, 
	whatsapp_number VARCHAR(30) NOT NULL, 
	github_url VARCHAR(255) NOT NULL, 
	facebook_url VARCHAR(255) NOT NULL, 
	linkedin_url VARCHAR(255) NOT NULL, 
	cv_url VARCHAR(255) NOT NULL, 
	meta_description_ar VARCHAR(300) NOT NULL, 
	meta_description_en VARCHAR(300) NOT NULL, 
	created_at DATETIME NOT NULL, 
	updated_at DATETIME NOT NULL, 
	PRIMARY KEY (id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;


CREATE TABLE IF NOT EXISTS project_categories (
	id INTEGER NOT NULL AUTO_INCREMENT, 
	slug VARCHAR(80) NOT NULL, 
	name_ar VARCHAR(100) NOT NULL, 
	name_en VARCHAR(100) NOT NULL, 
	sort_order INTEGER NOT NULL, 
	PRIMARY KEY (id), 
	UNIQUE (slug)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;


CREATE TABLE IF NOT EXISTS sections (
	id INTEGER NOT NULL AUTO_INCREMENT, 
	`key` VARCHAR(30) NOT NULL, 
	is_visible BOOL NOT NULL, 
	sort_order INTEGER NOT NULL, 
	PRIMARY KEY (id), 
	UNIQUE (`key`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;


CREATE TABLE IF NOT EXISTS services (
	id INTEGER NOT NULL AUTO_INCREMENT, 
	title_ar VARCHAR(120) NOT NULL, 
	title_en VARCHAR(120) NOT NULL, 
	description_ar TEXT, 
	description_en TEXT, 
	icon VARCHAR(40) NOT NULL, 
	is_visible BOOL NOT NULL, 
	sort_order INTEGER NOT NULL, 
	PRIMARY KEY (id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;


CREATE TABLE IF NOT EXISTS skill_categories (
	id INTEGER NOT NULL AUTO_INCREMENT, 
	name_ar VARCHAR(100) NOT NULL, 
	name_en VARCHAR(100) NOT NULL, 
	icon VARCHAR(40) NOT NULL, 
	sort_order INTEGER NOT NULL, 
	PRIMARY KEY (id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;


CREATE TABLE IF NOT EXISTS timeline_entries (
	id INTEGER NOT NULL AUTO_INCREMENT, 
	kind VARCHAR(20) NOT NULL, 
	title_ar VARCHAR(200) NOT NULL, 
	title_en VARCHAR(200) NOT NULL, 
	organization_ar VARCHAR(200) NOT NULL, 
	organization_en VARCHAR(200) NOT NULL, 
	description_ar TEXT, 
	description_en TEXT, 
	start_date VARCHAR(30) NOT NULL, 
	end_date VARCHAR(30) NOT NULL, 
	link_url VARCHAR(255) NOT NULL, 
	is_visible BOOL NOT NULL, 
	sort_order INTEGER NOT NULL, 
	PRIMARY KEY (id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE INDEX ix_timeline_entries_kind ON timeline_entries (kind);

CREATE TABLE IF NOT EXISTS projects (
	id INTEGER NOT NULL AUTO_INCREMENT, 
	slug VARCHAR(150) NOT NULL, 
	category_id INTEGER, 
	title_ar VARCHAR(150) NOT NULL, 
	title_en VARCHAR(150) NOT NULL, 
	summary_ar VARCHAR(300) NOT NULL, 
	summary_en VARCHAR(300) NOT NULL, 
	description_ar TEXT, 
	description_en TEXT, 
	technologies VARCHAR(500) NOT NULL, 
	github_url VARCHAR(255) NOT NULL, 
	demo_url VARCHAR(255) NOT NULL, 
	project_date VARCHAR(30) NOT NULL, 
	is_featured BOOL NOT NULL, 
	is_published BOOL NOT NULL, 
	sort_order INTEGER NOT NULL, 
	created_at DATETIME NOT NULL, 
	updated_at DATETIME NOT NULL, 
	PRIMARY KEY (id), 
	UNIQUE (slug), 
	FOREIGN KEY(category_id) REFERENCES project_categories (id) ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE INDEX ix_projects_category_id ON projects (category_id);

CREATE TABLE IF NOT EXISTS skills (
	id INTEGER NOT NULL AUTO_INCREMENT, 
	category_id INTEGER NOT NULL, 
	name VARCHAR(80) NOT NULL, 
	level VARCHAR(20) NOT NULL, 
	sort_order INTEGER NOT NULL, 
	PRIMARY KEY (id), 
	FOREIGN KEY(category_id) REFERENCES skill_categories (id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE INDEX ix_skills_category_id ON skills (category_id);

CREATE TABLE IF NOT EXISTS project_images (
	id INTEGER NOT NULL AUTO_INCREMENT, 
	project_id INTEGER NOT NULL, 
	path VARCHAR(255) NOT NULL, 
	thumb_path VARCHAR(255) NOT NULL, 
	caption_ar VARCHAR(200) NOT NULL, 
	caption_en VARCHAR(200) NOT NULL, 
	sort_order INTEGER NOT NULL, 
	PRIMARY KEY (id), 
	FOREIGN KEY(project_id) REFERENCES projects (id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE INDEX ix_project_images_project_id ON project_images (project_id);

-- Default section rows (visibility & order of the home page).
INSERT IGNORE INTO sections (`key`, is_visible, sort_order) VALUES
  ('about',1,1),('skills',1,2),('services',1,3),('projects',1,4),
  ('timeline',1,5),('gallery',1,6),('contact',1,7);
INSERT INTO profile (full_name_ar, full_name_en, display_name, brand_name, title_ar, title_en,
  tagline_ar, tagline_en, is_available, availability_ar, availability_en, specialization_ar,
  specialization_en, qualification_ar, qualification_en, location_ar, location_en, email,
  whatsapp_number, github_url, facebook_url, linkedin_url, cv_url, meta_description_ar,
  meta_description_en, created_at, updated_at)
SELECT '','','','','','','','',1,'','','','','','','','','','','','','','','','',NOW(),NOW()
WHERE NOT EXISTS (SELECT 1 FROM profile);

-- The admin account is created with:  flask create-admin
-- (passwords are hashed by the application and never stored in this file).
