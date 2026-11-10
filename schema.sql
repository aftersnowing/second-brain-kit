-- second brain DB 스키마 (2026-11-10 운영 판에서 sqlite_master 로 뽑음 — 구조만, 내용 없음)
-- FTS5 그림자 테이블(_data · _idx · _docsize · _config · _content)과 일회성 백업 테이블은 뺐다.

-- ===== results/brain.sqlite =====
CREATE TABLE attachment_lineage (
  base TEXT, filename TEXT, version TEXT, lang TEXT, ext TEXT, msg_id INTEGER,
  direction TEXT, counterpart TEXT, utc INTEGER, size INTEGER,
  folder_sn INTEGER, mail_sn INTEGER, subject TEXT);
CREATE TABLE attachments (
  msg_id INTEGER NOT NULL, filename TEXT, content_type TEXT,
  size INTEGER, content_sn INTEGER, text_extracted TEXT
);
CREATE TABLE build_meta (key TEXT PRIMARY KEY, value TEXT, utc INTEGER);
CREATE TABLE counterparts (
  addr TEXT PRIMARY KEY, name TEXT, domain TEXT, is_internal INTEGER,
  n_out INTEGER, n_in INTEGER, n_threads INTEGER, first_utc INTEGER, last_utc INTEGER,
  greeting TEXT, greeting_n INTEGER, opener TEXT, closing TEXT, closing_n INTEGER,
  self_intro INTEGER, lang TEXT, open_me INTEGER, open_them INTEGER, open_cc INTEGER);
CREATE TABLE entities (
  id INTEGER PRIMARY KEY, type TEXT, canonical TEXT, nick TEXT, imo TEXT,
  hull TEXT, company TEXT, UNIQUE(type, canonical));
CREATE TABLE entity_tag_meta (key TEXT PRIMARY KEY, value TEXT);
CREATE TABLE entity_tag_state (msg_id INTEGER PRIMARY KEY, fp BLOB);
CREATE TABLE fts_done (id INTEGER PRIMARY KEY, has_body INTEGER);
CREATE TABLE message_addresses (
  msg_id INTEGER NOT NULL, kind TEXT NOT NULL, name TEXT, addr TEXT
);
CREATE TABLE message_entities (
  msg_id INTEGER, entity_id INTEGER, evidence TEXT, hits INTEGER,
  UNIQUE(msg_id, entity_id));
CREATE TABLE messages (
  id            INTEGER PRIMARY KEY,
  mail_sn       INTEGER NOT NULL,
  folder_sn     INTEGER NOT NULL,
  folder_name   TEXT,
  message_id    TEXT,
  thread_id     TEXT,
  thread_count  INTEGER,
  subject       TEXT,
  subject_norm  TEXT,
  from_name     TEXT,
  from_email    TEXT,
  direction     TEXT,          -- out / in
  received_utc  INTEGER,
  sent_utc      INTEGER,
  size          INTEGER,
  attach_count  INTEGER,
  priority      INTEGER,
  security_level TEXT,
  spam_type     TEXT,
  to_me         INTEGER,
  from_external INTEGER,
  preview       TEXT,
  body_text     TEXT,          -- 패스2 후반에 채움
  body_own      TEXT,          -- 인용 제거한 본인 작성분 (문체용)
  has_body      INTEGER DEFAULT 0, in_reply_to TEXT, references_json TEXT,
  UNIQUE(folder_sn, mail_sn)
);
CREATE VIRTUAL TABLE messages_fts USING fts5(subject, from_name, from_email, folder_name, attach_names, preview, body_text, content='', contentless_delete=1, tokenize='trigram');
CREATE VIRTUAL TABLE messages_fts2 USING fts5(subject, from_name, from_email, folder_name, attach_names, preview, body_text, content='', contentless_delete=1, tokenize="unicode61 remove_diacritics 2", prefix='2 3 4');
CREATE TABLE notes (
  id TEXT PRIMARY KEY, utc INTEGER, kind TEXT, who TEXT, links TEXT,
  req INTEGER DEFAULT 0, due TEXT, body TEXT, file TEXT, done TEXT);
CREATE VIRTUAL TABLE notes_fts USING fts5(nid, body, who, tokenize='trigram');
CREATE TABLE open_loops (
  thread_id TEXT PRIMARY KEY, kind TEXT, last_msg_id INTEGER, last_utc INTEGER,
  n_msgs INTEGER, counterpart TEXT, subject TEXT, folder TEXT, days_open INTEGER, snippet TEXT,
  my_role TEXT, expired INTEGER DEFAULT 0, expiry_hint TEXT);
CREATE TABLE recurring_work (
  subject_norm TEXT PRIMARY KEY, n INTEGER, n_out INTEGER, n_threads INTEGER,
  first_utc INTEGER, last_utc INTEGER,
  median_gap_days REAL, regular INTEGER, counterparts TEXT, last_folder TEXT);
CREATE TABLE unsent (msg_id INTEGER PRIMARY KEY, folder_sn INTEGER, mail_sn INTEGER, reason TEXT);
CREATE INDEX ix_addr_addr ON message_addresses(addr);
CREATE INDEX ix_addr_msg  ON message_addresses(msg_id);
CREATE INDEX ix_al_base ON attachment_lineage(base, utc);
CREATE INDEX ix_al_file ON attachment_lineage(filename);
CREATE INDEX ix_att_msg  ON attachments(msg_id);
CREATE INDEX ix_att_name ON attachments(filename);
CREATE INDEX ix_cp_out ON counterparts(n_out DESC);
CREATE INDEX ix_me_ent ON message_entities(entity_id);
CREATE INDEX ix_me_msg ON message_entities(msg_id);
CREATE INDEX ix_msg_folder ON messages(folder_sn);
CREATE INDEX ix_msg_from   ON messages(from_email);
CREATE INDEX ix_msg_recv   ON messages(received_utc);
CREATE INDEX ix_msg_subjn  ON messages(subject_norm);
CREATE INDEX ix_msg_thread ON messages(thread_id);
CREATE INDEX ix_ol_kind ON open_loops(kind, days_open);
CREATE INDEX ix_rw_n ON recurring_work(n DESC);

-- ===== results/semantic.sqlite =====
CREATE TABLE meta (k TEXT PRIMARY KEY, v TEXT);
CREATE TABLE vecs (
  msg_id    INTEGER PRIMARY KEY,
  thread_id TEXT,
  vec       BLOB NOT NULL);
CREATE INDEX vecs_thread ON vecs(thread_id);

-- ===== results/attachments.sqlite =====
CREATE TABLE files (
  key        TEXT PRIMARY KEY,      -- filename|size (중복 제거 단위)
  filename   TEXT, size INTEGER, ext TEXT,
  mail_sn    INTEGER, content_sn INTEGER,   -- 실제로 받아온 출처 1건
  sha256     TEXT, path TEXT, bytes INTEGER, mime TEXT,
  status     TEXT,                  -- ok | size_mismatch | bigfile | http | magic | error
  err        TEXT, fetched_utc INTEGER);
CREATE TABLE texts (
  sha256 TEXT PRIMARY KEY, ext TEXT, chars INTEGER, units INTEGER,
  status TEXT,            -- ok | empty | scanned | unsupported | error
  err TEXT, parsed_utc INTEGER, text TEXT);
CREATE VIRTUAL TABLE texts_fts USING fts5(sha256 UNINDEXED, filename, body, tokenize='trigram');
CREATE INDEX files_status ON files(status);
CREATE INDEX texts_status ON texts(status);

-- ===== results/attachment_texts.sqlite =====
CREATE TABLE texts (
  sha256 TEXT PRIMARY KEY, ext TEXT, chars INTEGER, units INTEGER,
  status TEXT,            -- ok | empty | scanned | unsupported | error
  err TEXT, parsed_utc INTEGER, text TEXT);
CREATE VIRTUAL TABLE "texts_fts"
                USING fts5(sha256 UNINDEXED, filename, body, tokenize='trigram');
CREATE INDEX texts_status ON texts(status);

-- ===== results/work_index.sqlite =====
CREATE TABLE chunks (id INTEGER PRIMARY KEY, path TEXT, kind TEXT, ref TEXT, text TEXT, h TEXT);
CREATE TABLE item_entities (path TEXT, entity_id INTEGER, hits INTEGER, PRIMARY KEY (path, entity_id));
CREATE TABLE items (path TEXT PRIMARY KEY, cls TEXT, row TEXT, status TEXT, updated TEXT, exists_ INTEGER, n_docs INTEGER);
CREATE TABLE meta (k TEXT PRIMARY KEY, v TEXT);
CREATE TABLE suggest_cache (ptr TEXT, sig TEXT, js TEXT, PRIMARY KEY (ptr, sig));
CREATE TABLE vec_cache (h TEXT PRIMARY KEY, vec BLOB);

-- ===== results/kg.sqlite =====
CREATE TABLE alias(norm TEXT,node_id TEXT REFERENCES nodes(id),PRIMARY KEY(norm,node_id));
CREATE TABLE edges(src TEXT REFERENCES nodes(id),rel TEXT CHECK(rel IN ('CONTRASTS-WITH','COUNTERPART','DERIVED-FROM','EVIDENCE','INVOLVES','PENDING-ON','RAISED-BY','RELATES-TO-CASE','RESOLVED-BY','SUPERSEDES')),dst TEXT REFERENCES nodes(id),ptr TEXT NOT NULL CHECK(length(ptr)>0),at_utc INTEGER,attrs TEXT,UNIQUE(src,rel,dst,ptr,attrs));
CREATE TABLE meta(k TEXT PRIMARY KEY,v TEXT);
CREATE TABLE nodes(id TEXT PRIMARY KEY,type TEXT,label TEXT,attrs TEXT);
CREATE INDEX edges_dst ON edges(dst);
CREATE INDEX edges_ptr ON edges(ptr);
CREATE INDEX edges_src ON edges(src);
CREATE INDEX nodes_type ON nodes(type);
