-------------------------------
-- 一、内部数据源 (Internal Data Sources)
-------------------------------

-- 1. CRM系统 (客户关系管理)
CREATE TABLE crm_customer (
    customer_id VARCHAR(64) NOT NULL PRIMARY KEY,
    name VARCHAR(100),
    gender VARCHAR(10),
    phone VARCHAR(50),
    email VARCHAR(255),
    birthday VARCHAR(20), -- 使用VARCHAR以容纳不同格式的日期
    address TEXT,
    create_time TIMESTAMP,
    update_time TIMESTAMP,
    is_deleted SMALLINT DEFAULT 0
);

COMMENT ON TABLE crm_customer IS 'CRM客户基本信息表';
-- ... 其他注释保持不变

-- 2. 订单系统 (先创建主表)
CREATE TABLE oms_order (
    order_id VARCHAR(64) NOT NULL PRIMARY KEY,
    order_channel VARCHAR(32),
    customer_code VARCHAR(64),
    order_amount DECIMAL(10,2),
    discount_amount DECIMAL(10,2),
    pay_amount DECIMAL(10,2),
    order_status INTEGER,
    province VARCHAR(50),
    city VARCHAR(50),
    district VARCHAR(50),
    detail_address TEXT,
    order_time TIMESTAMP
);

COMMENT ON TABLE oms_order IS '订单主表';
-- ... 其他注释保持不变

-- 然后创建引用oms_order的表
CREATE TABLE oms_order_item (
    id BIGSERIAL PRIMARY KEY,
    order_id VARCHAR(64) NOT NULL REFERENCES oms_order(order_id),
    product_sku VARCHAR(64),
    product_name VARCHAR(255),
    quantity INTEGER,
    price DECIMAL(10,2)
);

COMMENT ON TABLE oms_order_item IS '订单商品明细表';
-- ... 其他注释保持不变

-- 3. 物流系统
CREATE TABLE lms_shipment (
    shipment_id VARCHAR(64) NOT NULL PRIMARY KEY,
    order_id VARCHAR(64) NOT NULL REFERENCES oms_order(order_id),
    carrier VARCHAR(50),
    sender_address TEXT,
    receiver_info TEXT,
    current_status VARCHAR(20),
    shipping_time TIMESTAMP,
    estimated_delivery DATE,
    actual_delivery TIMESTAMP
);

COMMENT ON TABLE lms_shipment IS '物流配送信息表';
-- ... 其他注释保持不变

-- 4. 财务系统
CREATE TABLE fms_financial_transaction (
    transaction_id VARCHAR(64) NOT NULL PRIMARY KEY,
    order_id VARCHAR(64) NOT NULL REFERENCES oms_order(order_id),
    payment_method VARCHAR(32),
    transaction_type INTEGER,
    transaction_amount DECIMAL(15,2),
    transaction_status VARCHAR(20),
    transaction_time TIMESTAMP
);

COMMENT ON TABLE fms_financial_transaction IS '财务交易流水表';
-- ... 其他注释保持不变

-------------------------------
-- 二、外部采购数据 (External Purchased Data)
-------------------------------

-- 1. 第三方市场报告数据
CREATE TABLE ext_market_trend (
    id BIGSERIAL PRIMARY KEY,
    period VARCHAR(10),
    region VARCHAR(50),
    category VARCHAR(100),
    market_size DECIMAL(15,2),
    growth_rate DECIMAL(5,2),
    data_source VARCHAR(255)
);

COMMENT ON TABLE ext_market_trend IS '第三方市场趋势数据';
-- ... 其他注释保持不变

-------------------------------
-- 三、爬虫数据 (Web Crawler Data)
-------------------------------

-- 1. 竞争对手价格数据
CREATE TABLE crawler_competitor_price (
    id BIGSERIAL PRIMARY KEY,
    crawl_time TIMESTAMP,
    platform VARCHAR(20),
    competitor_name VARCHAR(50),
    product_name VARCHAR(255),
    product_sku VARCHAR(64),
    price DECIMAL(10,2),
    promotion_info TEXT,
    is_in_stock SMALLINT
);

COMMENT ON TABLE crawler_competitor_price IS '竞争对手价格爬虫数据';
-- ... 其他注释保持不变