

-- ==========================================
-- TABLA: PARTICIPANTES
-- ==========================================
CREATE TABLE participants (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    email VARCHAR(255) UNIQUE NOT NULL,
    phone VARCHAR(20),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ==========================================
-- TABLA: COMPRAS
-- ==========================================
CREATE TABLE purchases (
    id SERIAL PRIMARY KEY,
    invoice_id VARCHAR(255) UNIQUE NOT NULL,
    participant_id INTEGER NOT NULL,
    amount DECIMAL(10,2) NOT NULL,
    email VARCHAR(255) NOT NULL,
    quantity INTEGER NOT NULL,
    status VARCHAR(50) DEFAULT 'pending',
    payment_method VARCHAR(50),
    transaction_id VARCHAR(255),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    confirmed_at TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_participant FOREIGN KEY(participant_id) REFERENCES participants(id) ON DELETE CASCADE
);

-- ==========================================
-- TABLA: NÚMEROS ASIGNADOS
-- ==========================================
CREATE TABLE assigned_numbers (
    id SERIAL PRIMARY KEY,
    number INTEGER UNIQUE NOT NULL,
    purchase_id INTEGER NOT NULL,
    participant_id INTEGER NOT NULL,
    assigned_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    status VARCHAR(50) DEFAULT 'active',
    CONSTRAINT fk_purchase FOREIGN KEY(purchase_id) REFERENCES purchases(id) ON DELETE CASCADE,
    CONSTRAINT fk_participant_num FOREIGN KEY(participant_id) REFERENCES participants(id) ON DELETE CASCADE
);

-- ==========================================
-- TABLA: TRANSACCIONES EPAYCO
-- ==========================================
CREATE TABLE epayco_transactions (
    id SERIAL PRIMARY KEY,
    ref_payco VARCHAR(255) UNIQUE NOT NULL,
    transaction_id VARCHAR(255),
    transaction_state VARCHAR(50),
    amount DECIMAL(10,2),
    currency VARCHAR(3),
    customer_email VARCHAR(255),
    purchase_id INTEGER,
    raw_data TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_purchase_epayco FOREIGN KEY(purchase_id) REFERENCES purchases(id)
);

-- Relaciones:
-- - participants (1) --- (N) purchases
-- - purchases (1) --- (N) assigned_numbers
-- - participants (1) --- (N) assigned_numbers
-- - purchases (1) --- (N) epayco_transactions

-- ==========================================
-- TABLA: USUARIOS/PARTICIPANTES
-- ==========================================
CREATE TABLE IF NOT EXISTS participants (
    id SERIAL PRIMARY KEY,
    email VARCHAR(255) UNIQUE NOT NULL,
    name VARCHAR(255),
    phone VARCHAR(20),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ==========================================
-- TABLA: COMPRAS/TRANSACCIONES
-- ==========================================
CREATE TABLE IF NOT EXISTS purchases (
    id SERIAL PRIMARY KEY,
    invoice_id VARCHAR(255) UNIQUE NOT NULL,
    participant_id INTEGER REFERENCES participants(id) ON DELETE CASCADE,
    amount DECIMAL(10,2) NOT NULL,
    email VARCHAR(255) NOT NULL,
    numbers TEXT NOT NULL,
    quantity INTEGER NOT NULL DEFAULT 4,
    status VARCHAR(50) DEFAULT 'pending',
    payment_method VARCHAR(50),
    transaction_id VARCHAR(255),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    confirmed_at TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ==========================================
-- TABLA: NÚMEROS ASIGNADOS
-- ==========================================
CREATE TABLE IF NOT EXISTS assigned_numbers (
    id SERIAL PRIMARY KEY,
    number INTEGER UNIQUE NOT NULL,
    invoice_id VARCHAR(255) NOT NULL REFERENCES purchases(invoice_id) ON DELETE CASCADE,
    participant_id INTEGER REFERENCES participants(id) ON DELETE SET NULL,
    assigned_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    status VARCHAR(50) DEFAULT 'active'
);

-- ==========================================
-- TABLA: TRANSACCIONES EPAYCO
-- ==========================================
CREATE TABLE IF NOT EXISTS epayco_transactions (
    id SERIAL PRIMARY KEY,
    ref_payco VARCHAR(255) UNIQUE NOT NULL,
    transaction_id VARCHAR(255),
    transaction_state VARCHAR(50),
    amount DECIMAL(10,2),
    currency VARCHAR(3),
    customer_email VARCHAR(255),
    invoice_id VARCHAR(255) REFERENCES purchases(invoice_id),
    raw_data TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ==========================================
-- TABLA: AUDITORÍA
-- ==========================================
CREATE TABLE IF NOT EXISTS audit_log (
    id SERIAL PRIMARY KEY,
    action VARCHAR(255) NOT NULL,
    entity_type VARCHAR(100),
    entity_id INTEGER,
    details TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ==========================================
-- ÍNDICES PARA RENDIMIENTO
-- ==========================================
CREATE INDEX IF NOT EXISTS idx_purchases_invoice_id ON purchases(invoice_id);
CREATE INDEX IF NOT EXISTS idx_purchases_status ON purchases(status);
CREATE INDEX IF NOT EXISTS idx_purchases_created_at ON purchases(created_at);
CREATE INDEX IF NOT EXISTS idx_purchases_participant_id ON purchases(participant_id);

CREATE INDEX IF NOT EXISTS idx_assigned_numbers_number ON assigned_numbers(number);
CREATE INDEX IF NOT EXISTS idx_assigned_numbers_invoice_id ON assigned_numbers(invoice_id);
CREATE INDEX IF NOT EXISTS idx_assigned_numbers_participant_id ON assigned_numbers(participant_id);
CREATE INDEX IF NOT EXISTS idx_assigned_numbers_status ON assigned_numbers(status);

CREATE INDEX IF NOT EXISTS idx_participants_email ON participants(email);

CREATE INDEX IF NOT EXISTS idx_epayco_ref_payco ON epayco_transactions(ref_payco);
CREATE INDEX IF NOT EXISTS idx_epayco_invoice_id ON epayco_transactions(invoice_id);

-- ==========================================
-- INICIALIZAR NÚMEROS DEL 1 AL 2000
-- ==========================================
-- Se insertarán a través de la aplicación cuando se necesite

-- ==========================================
-- RESTRICCIONES Y CONFIGURACIÓN
-- ==========================================
-- Máximo de números en la rifa
-- SELECT COUNT(*) FROM assigned_numbers; -- Debe ser <= 2000
