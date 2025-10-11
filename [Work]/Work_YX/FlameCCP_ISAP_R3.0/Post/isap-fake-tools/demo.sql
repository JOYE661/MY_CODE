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
COMMENT ON COLUMN crm_customer.customer_id IS '客户ID（与其他系统格式不一致）';
COMMENT ON COLUMN crm_customer.name IS '客户姓名';
COMMENT ON COLUMN crm_customer.gender IS '性别（值域不统一：0/1, 男/女, M/F）';
COMMENT ON COLUMN crm_customer.phone IS '手机号（可能存在格式不一致或错误）';
COMMENT ON COLUMN crm_customer.email IS '邮箱（可能存在无效格式）';
COMMENT ON COLUMN crm_customer.birthday IS '生日（日期格式不统一）';
COMMENT ON COLUMN crm_customer.address IS '地址（非标准结构，难以解析）';
COMMENT ON COLUMN crm_customer.create_time IS '创建时间';
COMMENT ON COLUMN crm_customer.update_time IS '更新时间';
COMMENT ON COLUMN crm_customer.is_deleted IS '逻辑删除标志（0：否，1：是）';

CREATE TABLE oms_order_item (
    id BIGSERIAL PRIMARY KEY,
    order_id VARCHAR(64) NOT NULL REFERENCES oms_order(order_id),
    product_sku VARCHAR(64),
    product_name VARCHAR(255),
    quantity INTEGER,
    price DECIMAL(10,2)
);

COMMENT ON TABLE oms_order_item IS '订单商品明细表';
COMMENT ON COLUMN oms_order_item.id IS '自增主键';
COMMENT ON COLUMN oms_order_item.order_id IS '关联订单ID';
COMMENT ON COLUMN oms_order_item.product_sku IS '商品SKU编码';
COMMENT ON COLUMN oms_order_item.product_name IS '商品名称（可能与主数据不一致）';
COMMENT ON COLUMN oms_order_item.quantity IS '购买数量';
COMMENT ON COLUMN oms_order_item.price IS '商品单价';



-- 2. 订单系统
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
COMMENT ON COLUMN oms_order.order_id IS '订单编号';
COMMENT ON COLUMN oms_order.order_channel IS '下单渠道（小程序、线下店等）';
COMMENT ON COLUMN oms_order.customer_code IS '客户编码（与CRM的customer_id关联键不一致）';
COMMENT ON COLUMN oms_order.order_amount IS '订单金额';
COMMENT ON COLUMN oms_order.discount_amount IS '优惠金额';
COMMENT ON COLUMN oms_order.pay_amount IS '实付金额';
COMMENT ON COLUMN oms_order.order_status IS '订单状态（需关联字典表解析：1待支付，2已支付，3已发货，4已完成，5已取消）';
COMMENT ON COLUMN oms_order.province IS '收货地址省';
COMMENT ON COLUMN oms_order.city IS '收货地址市';
COMMENT ON COLUMN oms_order.district IS '收货地址区';
COMMENT ON COLUMN oms_order.detail_address IS '详细地址（自由文本，可能与省市区字段冗余或冲突）';
COMMENT ON COLUMN oms_order.order_time IS '下单时间';



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
COMMENT ON COLUMN lms_shipment.shipment_id IS '运单号';
COMMENT ON COLUMN lms_shipment.order_id IS '关联订单ID';
COMMENT ON COLUMN lms_shipment.carrier IS '物流公司代码';
COMMENT ON COLUMN lms_shipment.sender_address IS '发货地址（非标准化）';
COMMENT ON COLUMN lms_shipment.receiver_info IS '收件人信息（混杂在一个字段，难以解析）';
COMMENT ON COLUMN lms_shipment.current_status IS '当前状态（与其他系统定义可能不同）';
COMMENT ON COLUMN lms_shipment.shipping_time IS '发货时间';
COMMENT ON COLUMN lms_shipment.estimated_delivery IS '预计送达日期';
COMMENT ON COLUMN lms_shipment.actual_delivery IS '实际送达时间';



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
COMMENT ON COLUMN fms_financial_transaction.transaction_id IS '交易流水号';
COMMENT ON COLUMN fms_financial_transaction.order_id IS '关联订单ID';
COMMENT ON COLUMN fms_financial_transaction.payment_method IS '支付方式（alipay, wechat_pay等）';
COMMENT ON COLUMN fms_financial_transaction.transaction_type IS '交易类型（1：支付，2：退款）';
COMMENT ON COLUMN fms_financial_transaction.transaction_amount IS '交易金额';
COMMENT ON COLUMN fms_financial_transaction.transaction_status IS '交易状态（SUCCESS, FAILED等）';
COMMENT ON COLUMN fms_financial_transaction.transaction_time IS '交易时间';



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
COMMENT ON COLUMN ext_market_trend.period IS '报告周期（如2023-Q3）';
COMMENT ON COLUMN ext_market_trend.region IS '区域（划分可能与公司内部定义不同）';
COMMENT ON COLUMN ext_market_trend.category IS '产品品类';
COMMENT ON COLUMN ext_market_trend.market_size IS '市场规模（元）';
COMMENT ON COLUMN ext_market_trend.growth_rate IS '增长率（%）';
COMMENT ON COLUMN ext_market_trend.data_source IS '数据来源（如艾瑞咨询）';


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
COMMENT ON COLUMN crawler_competitor_price.crawl_time IS '爬取时间';
COMMENT ON COLUMN crawler_competitor_price.platform IS '电商平台（如jd.com, tmall.com）';
COMMENT ON COLUMN crawler_competitor_price.competitor_name IS '竞争对手店铺名';
COMMENT ON COLUMN crawler_competitor_price.product_name IS '商品名称（与内部名称不匹配，需模糊匹配）';
COMMENT ON COLUMN crawler_competitor_price.product_sku IS '商品SKU（通常无法获取，需通过名称映射）';
COMMENT ON COLUMN crawler_competitor_price.price IS '售价';
COMMENT ON COLUMN crawler_competitor_price.promotion_info IS '促销信息（非结构化文本）';
COMMENT ON COLUMN crawler_competitor_price.is_in_stock IS '是否有货（1：是，0：否）';