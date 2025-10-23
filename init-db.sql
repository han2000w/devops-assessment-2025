-- 영수증 테이블 생성 (더미)
CREATE TABLE IF NOT EXISTS receipts (
    id SERIAL PRIMARY KEY,
    receipt_id VARCHAR(50) UNIQUE NOT NULL,
    merchant_name VARCHAR(255),
    total_amount DECIMAL(10, 2),
    receipt_date DATE,
    image_url TEXT,
    status VARCHAR(50),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 영수증 항목 테이블 (더미)
CREATE TABLE IF NOT EXISTS receipt_items (
    id SERIAL PRIMARY KEY,
    receipt_id VARCHAR(50) REFERENCES receipts(receipt_id),
    item_name VARCHAR(255),
    quantity INTEGER,
    price DECIMAL(10, 2),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 인덱스 생성
CREATE INDEX idx_receipts_status ON receipts(status);
CREATE INDEX idx_receipts_date ON receipts(receipt_date);
CREATE INDEX idx_receipt_items_receipt_id ON receipt_items(receipt_id);

-- 샘플 데이터 삽입 (선택사항)
INSERT INTO receipts (receipt_id, merchant_name, total_amount, receipt_date, status) VALUES
('RCP-20250101-001', '스타벅스 강남점', 15000.00, '2025-01-01', 'processed'),
('RCP-20250102-002', '올리브영 홍대점', 32000.00, '2025-01-02', 'processed'),
('RCP-20250103-003', 'GS25 편의점', 8500.00, '2025-01-03', 'processed');

INSERT INTO receipt_items (receipt_id, item_name, quantity, price) VALUES
('RCP-20250101-001', '아메리카노', 2, 4500.00),
('RCP-20250101-001', '샌드위치', 1, 6000.00),
('RCP-20250102-002', '스킨케어 세트', 1, 25000.00),
('RCP-20250102-002', '립스틱', 1, 7000.00),
('RCP-20250103-003', '삼각김밥', 2, 3000.00),
('RCP-20250103-003', '음료수', 1, 2500.00);
