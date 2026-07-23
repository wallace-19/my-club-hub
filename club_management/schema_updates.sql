-- ================================================================
-- ClubHub — Schema Updates
-- Run these on an EXISTING installation to bring it up to date.
-- Safe to run on a live database (no DROP statements).
-- ================================================================

-- 2026-07 updates
ALTER TABLE admins
    ADD COLUMN IF NOT EXISTS club_name VARCHAR(150) NOT NULL DEFAULT 'My Club',
    ADD COLUMN IF NOT EXISTS club_type ENUM('sports','private','campus','fitness') NOT NULL DEFAULT 'sports';

ALTER TABLE members
    ADD COLUMN IF NOT EXISTS club_type ENUM('sports','private','campus','fitness') NOT NULL DEFAULT 'sports',
    ADD COLUMN IF NOT EXISTS membership_tier VARCHAR(50) DEFAULT 'Standard',
    ADD COLUMN IF NOT EXISTS renewal_date DATE NULL;

ALTER TABLE events
    ADD COLUMN IF NOT EXISTS instructor VARCHAR(100) NULL;

CREATE TABLE IF NOT EXISTS attendance (
    id         INT AUTO_INCREMENT PRIMARY KEY,
    event_id   INT NOT NULL,
    member_id  INT NOT NULL,
    marked_at  TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (event_id)  REFERENCES events(id)  ON DELETE CASCADE,
    FOREIGN KEY (member_id) REFERENCES members(id) ON DELETE CASCADE,
    UNIQUE KEY unique_attendance (event_id, member_id),
    INDEX idx_event_id  (event_id),
    INDEX idx_member_id (member_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
