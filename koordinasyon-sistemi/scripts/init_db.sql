-- Hive Coordinator - Veritabanı Başlatma
-- 9 milyar düğüm için optimize edilmiş şema

-- Performans ayarları
ALTER SYSTEM SET shared_buffers = '256MB';
ALTER SYSTEM SET work_mem = '64MB';
ALTER SYSTEM SET maintenance_work_mem = '128MB';
ALTER SYSTEM SET max_connections = 200;

-- Düğüm tablosu partitioning (seviyeye göre)
-- Seviye 0-3: Ana partition (doğrudan yönetilen ~1111 düğüm)
-- Seviye 4-6: Bölgesel partition (~1,111,000 düğüm)
-- Seviye 7-10: Dağıtık partition (~9,999,888,889 düğüm)

CREATE TABLE IF NOT EXISTS nodes (
    id BIGSERIAL,
    address VARCHAR(64) NOT NULL,
    path VARCHAR(128) NOT NULL,
    level INTEGER NOT NULL,
    parent_address VARCHAR(64),
    name VARCHAR(256),
    role VARCHAR(128),
    status VARCHAR(20) DEFAULT 'active',
    capacity INTEGER DEFAULT 100,
    current_load INTEGER DEFAULT 0,
    efficiency_score FLOAT DEFAULT 1.0,
    subtree_total_nodes BIGINT DEFAULT 1,
    subtree_active_nodes BIGINT DEFAULT 1,
    subtree_tasks_completed BIGINT DEFAULT 0,
    subtree_avg_efficiency FLOAT DEFAULT 1.0,
    created_at TIMESTAMP DEFAULT NOW(),
    last_heartbeat TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    metadata_json JSONB DEFAULT '{}',
    PRIMARY KEY (id, level)
) PARTITION BY RANGE (level);

-- Partitionlar
CREATE TABLE nodes_core PARTITION OF nodes FOR VALUES FROM (0) TO (4);
CREATE TABLE nodes_regional PARTITION OF nodes FOR VALUES FROM (4) TO (7);
CREATE TABLE nodes_local PARTITION OF nodes FOR VALUES FROM (7) TO (11);

-- İndeksler
CREATE UNIQUE INDEX idx_nodes_address ON nodes (address);
CREATE INDEX idx_nodes_path ON nodes USING btree (path text_pattern_ops);
CREATE INDEX idx_nodes_level_status ON nodes (level, status);
CREATE INDEX idx_nodes_parent ON nodes (parent_address);
CREATE INDEX idx_nodes_load ON nodes (current_load, capacity);

-- Görev tablosu
CREATE TABLE IF NOT EXISTS tasks (
    id BIGSERIAL PRIMARY KEY,
    task_uid VARCHAR(64) UNIQUE NOT NULL,
    parent_task_uid VARCHAR(64),
    title VARCHAR(512) NOT NULL,
    description TEXT,
    priority VARCHAR(20) DEFAULT 'medium',
    status VARCHAR(20) DEFAULT 'pending',
    assigned_to VARCHAR(64),
    created_by VARCHAR(64) NOT NULL,
    target_level INTEGER,
    created_at TIMESTAMP DEFAULT NOW(),
    deadline TIMESTAMP,
    started_at TIMESTAMP,
    completed_at TIMESTAMP,
    total_subtasks BIGINT DEFAULT 0,
    completed_subtasks BIGINT DEFAULT 0,
    progress_pct FLOAT DEFAULT 0.0,
    tags JSONB DEFAULT '[]',
    metadata_json JSONB DEFAULT '{}'
);

CREATE INDEX idx_tasks_status_priority ON tasks (status, priority);
CREATE INDEX idx_tasks_assigned ON tasks (assigned_to, status);
CREATE INDEX idx_tasks_parent ON tasks (parent_task_uid);

-- Mesaj tablosu
CREATE TABLE IF NOT EXISTS messages (
    id BIGSERIAL PRIMARY KEY,
    message_uid VARCHAR(64) UNIQUE NOT NULL,
    message_type VARCHAR(20) NOT NULL,
    sender_address VARCHAR(64) NOT NULL,
    recipient_address VARCHAR(64),
    broadcast_path VARCHAR(128),
    subject VARCHAR(512) NOT NULL,
    body TEXT,
    cascade_depth INTEGER DEFAULT 0,
    cascade_target INTEGER,
    cascade_reached BIGINT DEFAULT 0,
    is_read BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT NOW(),
    metadata_json JSONB DEFAULT '{}'
);

CREATE INDEX idx_messages_recipient ON messages (recipient_address, is_read);
CREATE INDEX idx_messages_type ON messages (message_type, created_at);

-- Metrik toplama tablosu
CREATE TABLE IF NOT EXISTS aggregated_metrics (
    id BIGSERIAL PRIMARY KEY,
    node_address VARCHAR(64) NOT NULL,
    period_start TIMESTAMP NOT NULL,
    period_end TIMESTAMP NOT NULL,
    tasks_created BIGINT DEFAULT 0,
    tasks_completed BIGINT DEFAULT 0,
    tasks_failed BIGINT DEFAULT 0,
    avg_completion_time_hours FLOAT DEFAULT 0,
    active_nodes BIGINT DEFAULT 0,
    idle_nodes BIGINT DEFAULT 0,
    offline_nodes BIGINT DEFAULT 0,
    avg_load_pct FLOAT DEFAULT 0,
    messages_sent BIGINT DEFAULT 0,
    escalations BIGINT DEFAULT 0,
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_metrics_node_period ON aggregated_metrics (node_address, period_start);

-- Otomatik güncelleme trigger'ı
CREATE OR REPLACE FUNCTION update_timestamp()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER nodes_update_timestamp
    BEFORE UPDATE ON nodes
    FOR EACH ROW EXECUTE FUNCTION update_timestamp();

COMMENT ON TABLE nodes IS 'Hiyerarşik düğüm yapısı - 10 seviye, 9 milyar+ kapasite';
COMMENT ON TABLE tasks IS 'Kademeli görev dağıtım sistemi';
COMMENT ON TABLE messages IS 'Kademeli mesajlaşma - O(log₁₀ N) yayılma';
