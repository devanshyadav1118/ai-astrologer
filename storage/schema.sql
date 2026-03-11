CREATE TABLE IF NOT EXISTS books (
    book_id TEXT PRIMARY KEY,
    title TEXT NOT NULL,
    author TEXT,
    tradition TEXT,
    language TEXT DEFAULT 'english',
    tier INTEGER NOT NULL,
    status TEXT DEFAULT 'pending',
    total_chunks INTEGER DEFAULT 0,
    processed_chunks INTEGER DEFAULT 0,
    total_rules INTEGER DEFAULT 0,
    total_yogas INTEGER DEFAULT 0,
    total_descriptions INTEGER DEFAULT 0,
    extraction_started TEXT,
    extraction_completed TEXT,
    notes TEXT,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
    updated_at TEXT
);

CREATE TABLE IF NOT EXISTS chunks (
    chunk_id TEXT PRIMARY KEY,
    book_id TEXT NOT NULL,
    chunk_number INTEGER NOT NULL,
    chapter TEXT,
    page_range TEXT,
    word_count INTEGER DEFAULT 0,
    status TEXT DEFAULT 'pending',
    extraction_time REAL,
    tokens_used INTEGER,
    warnings TEXT,
    error_message TEXT,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
    updated_at TEXT,
    FOREIGN KEY (book_id) REFERENCES books(book_id)
);

CREATE TABLE IF NOT EXISTS unknown_entities (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    entity_text TEXT NOT NULL,
    book_id TEXT NOT NULL,
    chunk_id TEXT,
    context TEXT,
    frequency INTEGER DEFAULT 1,
    review_status TEXT DEFAULT 'pending',
    resolution_notes TEXT,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
    resolved_at TEXT,
    FOREIGN KEY (book_id) REFERENCES books(book_id),
    FOREIGN KEY (chunk_id) REFERENCES chunks(chunk_id)
);

CREATE TABLE IF NOT EXISTS processing_log (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    book_id TEXT NOT NULL,
    chunk_id TEXT,
    event_type TEXT NOT NULL,
    message TEXT,
    details TEXT,
    timestamp TEXT DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (book_id) REFERENCES books(book_id),
    FOREIGN KEY (chunk_id) REFERENCES chunks(chunk_id)
);

CREATE INDEX IF NOT EXISTS idx_books_status ON books(status);
CREATE INDEX IF NOT EXISTS idx_chunks_book_status ON chunks(book_id, status);
CREATE INDEX IF NOT EXISTS idx_unknown_entities_status ON unknown_entities(review_status);
