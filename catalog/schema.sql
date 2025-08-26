PRAGMA journal_mode=WAL;
PRAGMA foreign_keys=ON;

CREATE TABLE IF NOT EXISTS minutes (
  id INTEGER PRIMARY KEY,
  meeting_date TEXT,
  committee TEXT,
  title TEXT,
  page_url TEXT UNIQUE,
  pdf_url TEXT,
  word_count INTEGER DEFAULT 0
);

CREATE TABLE IF NOT EXISTS agenda_items (
  id INTEGER PRIMARY KEY,
  minutes_id INTEGER NOT NULL,
  agenda_item TEXT NOT NULL,
  order_no INTEGER NOT NULL,
  FOREIGN KEY(minutes_id) REFERENCES minutes(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS speeches (
  id INTEGER PRIMARY KEY,
  minutes_id INTEGER NOT NULL,
  agenda_item_id INTEGER NOT NULL,
  speaker TEXT,
  role TEXT,
  speech_text TEXT NOT NULL,
  FOREIGN KEY(minutes_id) REFERENCES minutes(id) ON DELETE CASCADE,
  FOREIGN KEY(agenda_item_id) REFERENCES agenda_items(id) ON DELETE CASCADE
);

-- FTS5 external content
CREATE VIRTUAL TABLE IF NOT EXISTS speeches_fts
USING fts5(
  speech_text,
  content='speeches',
  content_rowid='id',
  tokenize='unicode61'
);

-- Sync triggers
CREATE TRIGGER IF NOT EXISTS speeches_ai AFTER INSERT ON speeches BEGIN
  INSERT INTO speeches_fts(rowid, speech_text)
  VALUES (new.id, new.speech_text);
END;

CREATE TRIGGER IF NOT EXISTS speeches_ad AFTER DELETE ON speeches BEGIN
  INSERT INTO speeches_fts(speeches_fts, rowid, speech_text)
  VALUES ('delete', old.id, old.speech_text);
END;

CREATE TRIGGER IF NOT EXISTS speeches_au AFTER UPDATE ON speeches BEGIN
  INSERT INTO speeches_fts(speeches_fts, rowid, speech_text)
  VALUES ('delete', old.id, old.speech_text);
  INSERT INTO speeches_fts(rowid, speech_text)
  VALUES (new.id, new.speech_text);
END;

-- Indexes
CREATE INDEX IF NOT EXISTS idx_minutes_date ON minutes(meeting_date);
CREATE INDEX IF NOT EXISTS idx_minutes_committee ON minutes(committee);
CREATE INDEX IF NOT EXISTS idx_ai_minutes ON agenda_items(minutes_id);
CREATE INDEX IF NOT EXISTS idx_sp_minutes ON speeches(minutes_id);

