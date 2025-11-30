-- PostgreSQL兼容版本
-- 字符编码: UTF-8

CREATE TABLE test_data_exchange_item_info (
  id BIGSERIAL NOT NULL PRIMARY KEY,
  sxbh VARCHAR(38),
  sxmd VARCHAR(20),
  bt VARCHAR(300),
  calledphone VARCHAR(48),
  callphone VARCHAR(48),
  created_time TIMESTAMP,
  djbm VARCHAR(255),
  djbmdm BIGINT,
  djjgdm VARCHAR(100),
  djjgjb VARCHAR(1),
  djjgmc VARCHAR(300),
  djr VARCHAR(50),
  djrdm BIGINT,
  djsj TIMESTAMP,
  fjsl SMALLINT,
  gkbz VARCHAR(2),
  hyfl VARCHAR(30),
  hyflmc VARCHAR(50),
  isbm VARCHAR(2),
  issq VARCHAR(2),
  nmbz VARCHAR(2),
  nrfl VARCHAR(30),
  tsnr TEXT,
  update_time TIMESTAMP,
  wtsd VARCHAR(256),
  wtsd_addr VARCHAR(100),
  sxrq TIMESTAMP,
  sxrs VARCHAR(10),
  sxxs VARCHAR(3),
  xm VARCHAR(48),
  fjbh VARCHAR(200),
  yjly VARCHAR(100),
  timestamp TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  local_timestamp TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

COMMENT ON TABLE test_data_exchange_item_info IS '业务库事项件表-切换后新';
COMMENT ON COLUMN test_data_exchange_item_info.id IS '事项ID';
COMMENT ON COLUMN test_data_exchange_item_info.sxbh IS '编号规则：类别+日期+6位随机码';
COMMENT ON COLUMN test_data_exchange_item_info.sxmd IS '事项目的：咨询、建议、申诉、求决';
COMMENT ON COLUMN test_data_exchange_item_info.bt IS '事项标题：事项形式+姓名+问题属地';
COMMENT ON COLUMN test_data_exchange_item_info.calledphone IS '被叫号码';
COMMENT ON COLUMN test_data_exchange_item_info.callphone IS '来电号码';
COMMENT ON COLUMN test_data_exchange_item_info.created_time IS '创建时间：数据生成时间';
COMMENT ON COLUMN test_data_exchange_item_info.djbm IS '登记部门';
COMMENT ON COLUMN test_data_exchange_item_info.djbmdm IS '登记部门代码';
COMMENT ON COLUMN test_data_exchange_item_info.djjgdm IS '登记机构代码';
COMMENT ON COLUMN test_data_exchange_item_info.djjgjb IS '登记机构级别：1、国家级 2、省级 3、市级 4、区级';
COMMENT ON COLUMN test_data_exchange_item_info.djjgmc IS '登记机构名称';
COMMENT ON COLUMN test_data_exchange_item_info.djr IS '登记人姓名';
COMMENT ON COLUMN test_data_exchange_item_info.djrdm IS '登记人代码';
COMMENT ON COLUMN test_data_exchange_item_info.djsj IS '登记时间：创建时间以后的1小时之内';
COMMENT ON COLUMN test_data_exchange_item_info.fjsl IS '附件数量：根据生成的附件来计算';
COMMENT ON COLUMN test_data_exchange_item_info.gkbz IS '是否公开：0：否 1：是';
COMMENT ON COLUMN test_data_exchange_item_info.hyfl IS '行业分类';
COMMENT ON COLUMN test_data_exchange_item_info.hyflmc IS '行业分类名称';
COMMENT ON COLUMN test_data_exchange_item_info.isbm IS '是否保密：0：否 1：是';
COMMENT ON COLUMN test_data_exchange_item_info.issq IS '是否涉企：0：否 1：是';
COMMENT ON COLUMN test_data_exchange_item_info.nmbz IS '是否匿名：0：否 1：是';
COMMENT ON COLUMN test_data_exchange_item_info.nrfl IS '内容分类';
COMMENT ON COLUMN test_data_exchange_item_info.tsnr IS '投诉内容：随机问题生成';
COMMENT ON COLUMN test_data_exchange_item_info.update_time IS '更新时间：数据更新后的更新时间';
COMMENT ON COLUMN test_data_exchange_item_info.wtsd IS '问题属地';
COMMENT ON COLUMN test_data_exchange_item_info.wtsd_addr IS '问题属地地址';
COMMENT ON COLUMN test_data_exchange_item_info.sxrq IS '事项日期：数据生成日期';
COMMENT ON COLUMN test_data_exchange_item_info.sxrs IS '事项人数：该投诉问题的人数';
COMMENT ON COLUMN test_data_exchange_item_info.sxxs IS '事项形式：信、访、网、电';
COMMENT ON COLUMN test_data_exchange_item_info.xm IS '姓名';
COMMENT ON COLUMN test_data_exchange_item_info.fjbh IS '附件编号：如果有对应文件，则对应文件的编码';
COMMENT ON COLUMN test_data_exchange_item_info.yjly IS '原件来源：101：人民网，102：国家政务服务平台，103：国家信访局';
COMMENT ON COLUMN test_data_exchange_item_info.timestamp IS '抽取增量时间戳';
COMMENT ON COLUMN test_data_exchange_item_info.local_timestamp IS '本地入库时间';

CREATE INDEX idx_item_info_update_time ON test_data_exchange_item_info(update_time);
CREATE INDEX idx_item_info_created_time ON test_data_exchange_item_info(created_time);
CREATE INDEX idx_item_info_sxbh ON test_data_exchange_item_info(sxbh);

CREATE TABLE test_data_exchange_people_info (
  id BIGSERIAL NOT NULL PRIMARY KEY,
  sxbh VARCHAR(38),
  xm VARCHAR(50),
  mz VARCHAR(2),
  sjh VARCHAR(20),
  xb VARCHAR(1),
  xh VARCHAR(3),
  yzbm VARCHAR(10),
  zjhm VARCHAR(20),
  zjlx VARCHAR(2),
  zy VARCHAR(2),
  zz VARCHAR(200),
  zzdm VARCHAR(100),
  zzmm VARCHAR(20),
  zzzw VARCHAR(100),
  create_time TIMESTAMP,
  update_time TIMESTAMP,
  timestamp TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

COMMENT ON TABLE test_data_exchange_people_info IS '事项人员表';
COMMENT ON COLUMN test_data_exchange_people_info.id IS '事项人ID';
COMMENT ON COLUMN test_data_exchange_people_info.sxbh IS '来自事项库的事项编号：同data_exchange_item_info的sxbh';
COMMENT ON COLUMN test_data_exchange_people_info.xm IS '事项人姓名：随机姓名，但序号为1时，姓名需要与data_exchange_item_info的xm一致';
COMMENT ON COLUMN test_data_exchange_people_info.mz IS '事项人民族：随机生成';
COMMENT ON COLUMN test_data_exchange_people_info.sjh IS '手机号码：随机生成';
COMMENT ON COLUMN test_data_exchange_people_info.xb IS '事项人性别：0：女 1：男';
COMMENT ON COLUMN test_data_exchange_people_info.xh IS '序号：按照123456...排序，序号数与data_exchange_item_info的【事项人数】一致';
COMMENT ON COLUMN test_data_exchange_people_info.yzbm IS '邮政编码：可为空';
COMMENT ON COLUMN test_data_exchange_people_info.zjhm IS '证件号码：证件号码，如果证件类型为身份证，则该号码需要进行数据校验';
COMMENT ON COLUMN test_data_exchange_people_info.zjlx IS '证件类型：1 居民身份证 2 军官证 3 士兵证 4 警官证 5 港澳台居民身份证 6 护照 7 户口薄 99 其它';
COMMENT ON COLUMN test_data_exchange_people_info.zy IS '职业：可为空';
COMMENT ON COLUMN test_data_exchange_people_info.zz IS '事项人详细住址';
COMMENT ON COLUMN test_data_exchange_people_info.zzdm IS '事项人住址行政区划代码：参考行政区划码表';
COMMENT ON COLUMN test_data_exchange_people_info.zzmm IS '政治面貌：可为空';
COMMENT ON COLUMN test_data_exchange_people_info.zzzw IS '事项人住址行政区划中文：参考行政区划码表（与zzdm保持映射一致）';
COMMENT ON COLUMN test_data_exchange_people_info.create_time IS '创建时间';
COMMENT ON COLUMN test_data_exchange_people_info.update_time IS '更新时间';
COMMENT ON COLUMN test_data_exchange_people_info.timestamp IS '抽取增量时间戳';

CREATE INDEX idx_people_info_sxbh ON test_data_exchange_people_info(sxbh);
CREATE INDEX idx_people_info_create_time ON test_data_exchange_people_info(create_time);

CREATE TABLE test_data_exchange_item_process_info (
  id BIGSERIAL NOT NULL PRIMARY KEY,
  sxbh VARCHAR(38),
  blfs VARCHAR(6),
  bljgdm VARCHAR(100),
  bljg VARCHAR(200),
  dept_id BIGINT,
  dept_name VARCHAR(200),
  user_id BIGINT,
  user_name VARCHAR(60),
  blsj TIMESTAMP,
  dfnr TEXT,
  fjsl BIGINT,
  fjbh BIGINT,
  update_time TIMESTAMP,
  create_time TIMESTAMP,
  timestamp TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  local_timestamp TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

COMMENT ON TABLE test_data_exchange_item_process_info IS '事项事项办理记录表';
COMMENT ON COLUMN test_data_exchange_item_process_info.id IS '主键id';
COMMENT ON COLUMN test_data_exchange_item_process_info.sxbh IS '事项编号';
COMMENT ON COLUMN test_data_exchange_item_process_info.blfs IS '办理方式';
COMMENT ON COLUMN test_data_exchange_item_process_info.bljgdm IS '办理机构代码';
COMMENT ON COLUMN test_data_exchange_item_process_info.bljg IS '办理机构';
COMMENT ON COLUMN test_data_exchange_item_process_info.dept_id IS '办理部门id';
COMMENT ON COLUMN test_data_exchange_item_process_info.dept_name IS '办理部门名称';
COMMENT ON COLUMN test_data_exchange_item_process_info.user_id IS '经办人id';
COMMENT ON COLUMN test_data_exchange_item_process_info.user_name IS '经办人';
COMMENT ON COLUMN test_data_exchange_item_process_info.blsj IS '办理时间';
COMMENT ON COLUMN test_data_exchange_item_process_info.dfnr IS '答复内容';
COMMENT ON COLUMN test_data_exchange_item_process_info.fjsl IS '附件数量';
COMMENT ON COLUMN test_data_exchange_item_process_info.fjbh IS '附件编号';
COMMENT ON COLUMN test_data_exchange_item_process_info.update_time IS '更新时间';
COMMENT ON COLUMN test_data_exchange_item_process_info.create_time IS '创建时间';
COMMENT ON COLUMN test_data_exchange_item_process_info.timestamp IS '抽取增量时间戳';
COMMENT ON COLUMN test_data_exchange_item_process_info.local_timestamp IS '抽取到本地时间';

CREATE INDEX idx_process_info_sxbh ON test_data_exchange_item_process_info(sxbh);
CREATE INDEX idx_process_info_create_time ON test_data_exchange_item_process_info(create_time);

CREATE TABLE test_data_exchange_sx_attach (
  id BIGSERIAL NOT NULL PRIMARY KEY,
  sxbh VARCHAR(64),
  link TEXT,
  name VARCHAR(500),
  original_name VARCHAR(500),
  extension VARCHAR(12),
  attach_size BIGINT,
  create_time TIMESTAMP,
  full_path TEXT,
  timestamp TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

COMMENT ON TABLE test_data_exchange_sx_attach IS '附件表';
COMMENT ON COLUMN test_data_exchange_sx_attach.id IS '主键';
COMMENT ON COLUMN test_data_exchange_sx_attach.sxbh IS '事项件编号';
COMMENT ON COLUMN test_data_exchange_sx_attach.link IS '附件地址';
COMMENT ON COLUMN test_data_exchange_sx_attach.name IS '附件名称';
COMMENT ON COLUMN test_data_exchange_sx_attach.original_name IS '附件原名';
COMMENT ON COLUMN test_data_exchange_sx_attach.extension IS '附件拓展名';
COMMENT ON COLUMN test_data_exchange_sx_attach.attach_size IS '附件大小';
COMMENT ON COLUMN test_data_exchange_sx_attach.create_time IS '创建时间';
COMMENT ON COLUMN test_data_exchange_sx_attach.full_path IS '文件完整路径';
COMMENT ON COLUMN test_data_exchange_sx_attach.timestamp IS '抽取增量时间戳';

CREATE INDEX idx_attach_create_time ON test_data_exchange_sx_attach(create_time);
CREATE INDEX idx_attach_sxbh ON test_data_exchange_sx_attach(sxbh);

CREATE TABLE test_data_exchange_ws_item_info (
  id BIGSERIAL NOT NULL PRIMARY KEY,
  sxbh VARCHAR(38),
  sxmd VARCHAR(20),
  bt VARCHAR(300),
  created_time TIMESTAMP,
  fjsl SMALLINT,
  gkbz VARCHAR(2),
  hyfl VARCHAR(30),
  hyflmc VARCHAR(50),
  isbm VARCHAR(2),
  issq VARCHAR(2),
  nmbz VARCHAR(2),
  nrfl VARCHAR(30),
  tsnr TEXT,
  update_time TIMESTAMP,
  wtsd VARCHAR(256),
  wtsd_addr VARCHAR(100),
  sxrq TIMESTAMP,
  sxrs VARCHAR(10),
  sxxs VARCHAR(3),
  xm VARCHAR(48),
  yjly VARCHAR(100),
  zjhm VARCHAR(100),
  sjh VARCHAR(100),
  zjlx VARCHAR(100),
  timestamp TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  local_timestamp TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

COMMENT ON TABLE test_data_exchange_ws_item_info IS '业务库事项件表-网上';
COMMENT ON COLUMN test_data_exchange_ws_item_info.id IS '事项ID';
COMMENT ON COLUMN test_data_exchange_ws_item_info.sxbh IS '编号规则：';
COMMENT ON COLUMN test_data_exchange_ws_item_info.sxmd IS '事项目的';
COMMENT ON COLUMN test_data_exchange_ws_item_info.bt IS '事项标题';
COMMENT ON COLUMN test_data_exchange_ws_item_info.created_time IS '创建时间';
COMMENT ON COLUMN test_data_exchange_ws_item_info.fjsl IS '附件数量';
COMMENT ON COLUMN test_data_exchange_ws_item_info.gkbz IS '是否公开0：否? 1: 是';
COMMENT ON COLUMN test_data_exchange_ws_item_info.hyfl IS '行业分类';
COMMENT ON COLUMN test_data_exchange_ws_item_info.hyflmc IS '行业分类名称';
COMMENT ON COLUMN test_data_exchange_ws_item_info.isbm IS '是否保密0：否? 1: 是';
COMMENT ON COLUMN test_data_exchange_ws_item_info.issq IS '是否涉企0：否? 1: 是';
COMMENT ON COLUMN test_data_exchange_ws_item_info.nmbz IS '是否匿名0：否? 1: 是';
COMMENT ON COLUMN test_data_exchange_ws_item_info.nrfl IS '内容分类';
COMMENT ON COLUMN test_data_exchange_ws_item_info.tsnr IS '投诉内容';
COMMENT ON COLUMN test_data_exchange_ws_item_info.update_time IS '更新时间';
COMMENT ON COLUMN test_data_exchange_ws_item_info.wtsd IS '问题属地';
COMMENT ON COLUMN test_data_exchange_ws_item_info.wtsd_addr IS '问题属地地址';
COMMENT ON COLUMN test_data_exchange_ws_item_info.sxrq IS '事项日期';
COMMENT ON COLUMN test_data_exchange_ws_item_info.sxrs IS '事项人数';
COMMENT ON COLUMN test_data_exchange_ws_item_info.sxxs IS '事项形式';
COMMENT ON COLUMN test_data_exchange_ws_item_info.xm IS '姓名';
COMMENT ON COLUMN test_data_exchange_ws_item_info.yjly IS '原件来源';
COMMENT ON COLUMN test_data_exchange_ws_item_info.zjhm IS '证件号码';
COMMENT ON COLUMN test_data_exchange_ws_item_info.sjh IS '手机号';
COMMENT ON COLUMN test_data_exchange_ws_item_info.zjlx IS '证件类型';
COMMENT ON COLUMN test_data_exchange_ws_item_info.timestamp IS '抽取增量时间戳';
COMMENT ON COLUMN test_data_exchange_ws_item_info.local_timestamp IS '本地入库时间';

CREATE INDEX idx_ws_item_info_update_time ON test_data_exchange_ws_item_info(update_time);
CREATE INDEX idx_ws_item_info_created_time ON test_data_exchange_ws_item_info(created_time);
CREATE INDEX idx_ws_item_info_sxbh ON test_data_exchange_ws_item_info(sxbh);

CREATE TABLE test_city_exchange_in_shaox_hotline_rxgd (
  caller_id VARCHAR(32) NOT NULL PRIMARY KEY,
  user_name VARCHAR(32) NOT NULL,
  gender VARCHAR(32) NOT NULL,
  id_type VARCHAR(32),
  id_no VARCHAR(32),
  called_phone VARCHAR(32) NOT NULL,
  tel_phone VARCHAR(32) NOT NULL,
  income_phone VARCHAR(32) NOT NULL,
  usual_address VARCHAR(1024),
  usual_address_id VARCHAR(12) NOT NULL,
  residence_address VARCHAR(1024),
  letter_date TIMESTAMP NOT NULL,
  company_tag VARCHAR(1),
  company_name VARCHAR(32),
  enrollment_method VARCHAR(32) NOT NULL,
  title VARCHAR(128) NOT NULL,
  letter_aim VARCHAR(32) NOT NULL,
  suggest_tag VARCHAR(1),
  content_type VARCHAR(32) NOT NULL,
  problem_source VARCHAR(12) NOT NULL,
  problem_occurrence VARCHAR(500) NOT NULL,
  open_tag VARCHAR(1) NOT NULL,
  anonymus_tag VARCHAR(5) NOT NULL,
  data_type VARCHAR(32) NOT NULL,
  cue_of_time TIMESTAMP,
  enrollment_id VARCHAR(32) NOT NULL,
  enrollment_name VARCHAR(32) NOT NULL,
  enrollment_time TIMESTAMP NOT NULL,
  enrollment_unit VARCHAR(32) NOT NULL,
  submit_content VARCHAR(2000) NOT NULL,
  reply_content VARCHAR(2000),
  created_time TIMESTAMP,
  updated_time TIMESTAMP,
  source_phone VARCHAR(32),
  industry_sort VARCHAR(32),
  zyhy VARCHAR(10),
  isbm VARCHAR(2) NOT NULL,
  jjcd VARCHAR(5) NOT NULL,
  sjly VARCHAR(12),
  yjly VARCHAR(3) NOT NULL,
  local_create_time TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  local_update_time TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

COMMENT ON TABLE test_city_exchange_in_shaox_hotline_rxgd IS '热线工单信息';
COMMENT ON COLUMN test_city_exchange_in_shaox_hotline_rxgd.caller_id IS '来电编号（主键）';
COMMENT ON COLUMN test_city_exchange_in_shaox_hotline_rxgd.user_name IS '姓名';
COMMENT ON COLUMN test_city_exchange_in_shaox_hotline_rxgd.gender IS '性别(0未知性别1男性2女性9未说明性别)';
COMMENT ON COLUMN test_city_exchange_in_shaox_hotline_rxgd.id_type IS '证件类型';
COMMENT ON COLUMN test_city_exchange_in_shaox_hotline_rxgd.id_no IS '证件号码';
COMMENT ON COLUMN test_city_exchange_in_shaox_hotline_rxgd.called_phone IS '被叫号码';
COMMENT ON COLUMN test_city_exchange_in_shaox_hotline_rxgd.tel_phone IS '联系电话';
COMMENT ON COLUMN test_city_exchange_in_shaox_hotline_rxgd.income_phone IS '来电号码';
COMMENT ON COLUMN test_city_exchange_in_shaox_hotline_rxgd.usual_address IS '常住地址';
COMMENT ON COLUMN test_city_exchange_in_shaox_hotline_rxgd.usual_address_id IS '常住地址代码';
COMMENT ON COLUMN test_city_exchange_in_shaox_hotline_rxgd.residence_address IS '户籍地址';
COMMENT ON COLUMN test_city_exchange_in_shaox_hotline_rxgd.letter_date IS '民呼日期';
COMMENT ON COLUMN test_city_exchange_in_shaox_hotline_rxgd.company_tag IS '是否为企业(0:否,1:是)';
COMMENT ON COLUMN test_city_exchange_in_shaox_hotline_rxgd.company_name IS '企业名称';
COMMENT ON COLUMN test_city_exchange_in_shaox_hotline_rxgd.enrollment_method IS '事项形式(电)';
COMMENT ON COLUMN test_city_exchange_in_shaox_hotline_rxgd.title IS '标题';
COMMENT ON COLUMN test_city_exchange_in_shaox_hotline_rxgd.letter_aim IS '事目的的';
COMMENT ON COLUMN test_city_exchange_in_shaox_hotline_rxgd.suggest_tag IS '是否建议(0:否,1:是)';
COMMENT ON COLUMN test_city_exchange_in_shaox_hotline_rxgd.content_type IS '内容分类';
COMMENT ON COLUMN test_city_exchange_in_shaox_hotline_rxgd.problem_source IS '问题属地代码(行政区划编码)';
COMMENT ON COLUMN test_city_exchange_in_shaox_hotline_rxgd.problem_occurrence IS '问题发生地';
COMMENT ON COLUMN test_city_exchange_in_shaox_hotline_rxgd.open_tag IS '是否公开(0:否,1:是)';
COMMENT ON COLUMN test_city_exchange_in_shaox_hotline_rxgd.anonymus_tag IS '是否匿名(0:否,1:是)';
COMMENT ON COLUMN test_city_exchange_in_shaox_hotline_rxgd.data_type IS '数据类型(1.人工服务2.智能服务)';
COMMENT ON COLUMN test_city_exchange_in_shaox_hotline_rxgd.cue_of_time IS '事项限办时间';
COMMENT ON COLUMN test_city_exchange_in_shaox_hotline_rxgd.enrollment_id IS '登记人ID';
COMMENT ON COLUMN test_city_exchange_in_shaox_hotline_rxgd.enrollment_name IS '登记人姓名';
COMMENT ON COLUMN test_city_exchange_in_shaox_hotline_rxgd.enrollment_time IS '登记时间';
COMMENT ON COLUMN test_city_exchange_in_shaox_hotline_rxgd.enrollment_unit IS '登记单位';
COMMENT ON COLUMN test_city_exchange_in_shaox_hotline_rxgd.submit_content IS '反映诉求内容';
COMMENT ON COLUMN test_city_exchange_in_shaox_hotline_rxgd.reply_content IS '处理情况';
COMMENT ON COLUMN test_city_exchange_in_shaox_hotline_rxgd.created_time IS '创建时间';
COMMENT ON COLUMN test_city_exchange_in_shaox_hotline_rxgd.updated_time IS '更新时间';
COMMENT ON COLUMN test_city_exchange_in_shaox_hotline_rxgd.source_phone IS '源被叫号码';
COMMENT ON COLUMN test_city_exchange_in_shaox_hotline_rxgd.industry_sort IS '行业内容分类';
COMMENT ON COLUMN test_city_exchange_in_shaox_hotline_rxgd.zyhy IS '专业行业';
COMMENT ON COLUMN test_city_exchange_in_shaox_hotline_rxgd.isbm IS '是否保密(0:否,1:是)';
COMMENT ON COLUMN test_city_exchange_in_shaox_hotline_rxgd.jjcd IS '紧急程度(1.快速2.一般)';
COMMENT ON COLUMN test_city_exchange_in_shaox_hotline_rxgd.sjly IS '数据来源(行政区划编码)';
COMMENT ON COLUMN test_city_exchange_in_shaox_hotline_rxgd.yjly IS '原件来源(热线12345各城市代码)';
COMMENT ON COLUMN test_city_exchange_in_shaox_hotline_rxgd.local_create_time IS '本地入库时间';
COMMENT ON COLUMN test_city_exchange_in_shaox_hotline_rxgd.local_update_time IS '本地更新时间';

-- 设置数据库字符集（在PostgreSQL中通常在建库时设置）
-- 建议在创建数据库时使用：CREATE DATABASE your_database_name ENCODING 'UTF8';
