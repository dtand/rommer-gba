BEGIN TRANSACTION;
CREATE TABLE IF NOT EXISTS "annotations" (
	"id"	INTEGER,
	"session_uuid"	TEXT NOT NULL,
	"frame_set_id"	INTEGER NOT NULL,
	"context"	TEXT,
	"scene"	TEXT,
	"tags"	TEXT,
	"description"	TEXT,
	"action_type"	TEXT,
	"intent"	TEXT,
	"outcome"	TEXT,
	"created_at"	TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
	PRIMARY KEY("id" AUTOINCREMENT),
	UNIQUE("session_uuid","frame_set_id"),
	FOREIGN KEY("session_uuid") REFERENCES "sessions"("session_uuid")
);
CREATE TABLE IF NOT EXISTS "frame_sets" (
	"id"	INTEGER,
	"session_uuid"	TEXT NOT NULL,
	"frame_set_id"	INTEGER NOT NULL,
	"timestamp"	INTEGER NOT NULL,
	"buttons"	TEXT NOT NULL,
	"frames_in_set"	TEXT NOT NULL,
	"created_at"	TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
	PRIMARY KEY("id" AUTOINCREMENT),
	UNIQUE("session_uuid","frame_set_id"),
	FOREIGN KEY("session_uuid") REFERENCES "sessions"("session_uuid")
);
CREATE TABLE IF NOT EXISTS "memory_changes" (
	"id"	INTEGER,
	"session_uuid"	TEXT NOT NULL,
	"frame_set_id"	INTEGER NOT NULL,
	"region"	TEXT NOT NULL,
	"frame"	INTEGER NOT NULL,
	"address"	TEXT NOT NULL,
	"prev_val"	TEXT NOT NULL,
	"curr_val"	TEXT NOT NULL,
	"freq"	INTEGER NOT NULL,
	"created_at"	TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
	PRIMARY KEY("id" AUTOINCREMENT),
	FOREIGN KEY("session_uuid") REFERENCES "sessions"("session_uuid")
);
CREATE TABLE IF NOT EXISTS "sessions" (
	"session_uuid"	TEXT,
	"created_at"	TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
	PRIMARY KEY("session_uuid")
);
CREATE TABLE IF NOT EXISTS "metadata" (
	"id"	INTEGER,
	"session_uuid"	TEXT NOT NULL,
	"created_at"	TEXT NOT NULL,
	"created_timestamp"	INTEGER NOT NULL,
	"total_frame_sets"	INTEGER NOT NULL,
	"num_frames_per_set"	INTEGER NOT NULL,
	"frame_set_id_min"	INTEGER NOT NULL,
	"frame_set_id_max"	INTEGER NOT NULL,
	"source_csv"	TEXT NOT NULL,
	"game_config"	TEXT NOT NULL,
	"game_name"	TEXT,
	"is_custom_name"	INTEGER NOT NULL DEFAULT 0,
	PRIMARY KEY("id" AUTOINCREMENT),
	UNIQUE("session_uuid"),
	FOREIGN KEY("session_uuid") REFERENCES "sessions"("session_uuid")
);
COMMIT;