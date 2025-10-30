CREATE TABLE `test_data_exchange_item_info` (
`id` bigint(20) NOT NULL COMMENT '事项ID',
`sxbh` varchar(38) DEFAULT NULL COMMENT '编号规则：',
`sxmd` varchar(20) DEFAULT NULL COMMENT '事项目的',
`bt` varchar(300) DEFAULT NULL COMMENT '事项标题',
`calledphone` varchar(48) DEFAULT NULL COMMENT '被叫号码',
`callphone` varchar(48) DEFAULT NULL COMMENT '来电号码',
`created_time` datetime(6) DEFAULT NULL COMMENT '创建时间',
`djbm` varchar(255) DEFAULT NULL COMMENT '登记部门',
`djbmdm` bigint(20) DEFAULT NULL COMMENT '登记部门代码',
`djjgdm` varchar(100) DEFAULT NULL COMMENT '登记机构代码',
`djjgjb` varchar(1) DEFAULT NULL COMMENT '1、国家级 2、省级 3、市级 4、区级',
`djjgmc` varchar(300) DEFAULT NULL COMMENT '登记机构名称',
`djr` varchar(50) DEFAULT NULL COMMENT '登记人姓名',
`djrdm` bigint(20) DEFAULT NULL COMMENT '登记人代码',
`djsj` datetime(6) DEFAULT NULL COMMENT '登记时间',
`fjsl` smallint(6) DEFAULT NULL COMMENT '附件数量',
`gkbz` varchar(2) DEFAULT NULL COMMENT '是否公开0：否? 1: 是',
`hyfl` varchar(30) DEFAULT NULL COMMENT '行业分类',
`hyflmc` varchar(50) DEFAULT NULL COMMENT '行业分类名称',
`isbm` varchar(2) DEFAULT NULL COMMENT '是否保密0：否? 1: 是',
`issq` varchar(2) DEFAULT NULL COMMENT '是否涉企0：否? 1: 是',
`nmbz` varchar(2) DEFAULT NULL COMMENT '是否匿名0：否? 1: 是',
`nrfl` varchar(30) DEFAULT NULL COMMENT '内容分类',
`tsnr` longtext COMMENT '投诉内容',
`update_time` datetime(6) DEFAULT NULL COMMENT 'None',
`wtsd` varchar(256) DEFAULT NULL COMMENT '问题属地',
`wtsd_addr` varchar(100) DEFAULT NULL COMMENT '问题属地地址',
`sxrq` datetime(6) DEFAULT NULL COMMENT '事项日期',
`sxrs` varchar(10) DEFAULT NULL COMMENT '事项人数',
`sxxs` varchar(3) DEFAULT NULL COMMENT '事项形式',
`xm` varchar(48) DEFAULT NULL COMMENT '姓名',
  fjbh varchar(200) DEFAULT NULL COMMENT '附件编号',
`yjly` varchar(100) DEFAULT NULL COMMENT '原件来源',
`timestamp` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '抽取增量时间戳',
`local_timestamp` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '本地入库时间',
PRIMARY KEY (`id`),
UNIQUE KEY `index_pkey_id` USING BTREE (`id`),
KEY `index_update_time` USING BTREE (`update_time`),
KEY `index_created_time` (`created_time`)
) ENGINE = InnoDB DEFAULT CHARSET = utf8mb4 COMMENT '业务库事项件表-切换后新';

CREATE TABLE `test_data_exchange_people_info` (
`id` bigint(20) NOT NULL COMMENT '事项人ID',
`sxbh` varchar(38) DEFAULT NULL COMMENT '来自事项库的事项编号',
`xm` varchar(50) DEFAULT NULL COMMENT '事项人姓名',
`mz` varchar(2) DEFAULT NULL COMMENT '事项人民族',
`sjh` varchar(20) DEFAULT NULL COMMENT '手机号码',
`xb` varchar(1) DEFAULT NULL COMMENT '事项人性别,0：女  1：男',
`xh` varchar(3) DEFAULT NULL COMMENT '序号',
`yzbm` varchar(10) DEFAULT NULL COMMENT '邮政编码',
`zjhm` varchar(20) DEFAULT NULL COMMENT '证件号码',
`zjlx` varchar(2) DEFAULT NULL COMMENT '证件类型',
`zy` varchar(2) DEFAULT NULL COMMENT '职业',
`zz` varchar(200) DEFAULT NULL COMMENT '事项人详细住址',
`zzdm` varchar(100) DEFAULT NULL COMMENT '事项人住址行政区划代码',
`zzmm` varchar(20) DEFAULT NULL COMMENT '政治面貌',
`zzzw` varchar(100) DEFAULT NULL COMMENT '事项人住址行政区划中文',
`create_time` datetime DEFAULT NULL COMMENT '创建时间',
`update_time` datetime DEFAULT NULL COMMENT '更新时间',
`timestamp` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '抽取增量时间戳'
PRIMARY KEY (`id`),
UNIQUE KEY `dwd_sx_people_info_pkey` USING BTREE (`id`),
KEY `auto_shard_key_sxbh` USING BTREE (`sxbh`)

)COMMENT '事项人员表';

CREATE TABLE `test_data_exchange_item_process_info` (
`id` bigint(20) NOT NULL COMMENT '主键id',
`sxbh` varchar(38) DEFAULT NULL COMMENT '事项编号',
`blfs` varchar(6) DEFAULT NULL COMMENT '办理方式',
`bljgdm` varchar(100) DEFAULT NULL COMMENT '办理机构代码',
`bljg` varchar(200) DEFAULT NULL COMMENT '办理机构',
`dept_id` bigint(20) DEFAULT NULL COMMENT '办理部门id',
`dept_name` varchar(200) DEFAULT NULL COMMENT '办理部门名称',
`user_id` bigint(20) DEFAULT NULL COMMENT '经办人id',
`user_name` varchar(60) DEFAULT NULL COMMENT '经办人',
`blsj` datetime DEFAULT NULL COMMENT '办理时间',
`dfnr` text COMMENT '答复内容',
`fjsl` bigint(20) DEFAULT NULL COMMENT '附件数量',
`fjbh` bigint(20) DEFAULT NULL COMMENT '附件编号',
`update_time` datetime DEFAULT NULL COMMENT '更新时间',
`create_time` datetime DEFAULT NULL COMMENT '创建时间',
`timestamp` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '抽取增量时间戳',
`local_timestamp` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '抽取到本地时间',
PRIMARY KEY (`id`),
UNIQUE KEY `visit_petition_process_pkey` USING BTREE (`id`),
KEY `auto_shard_key_id` USING BTREE (`id`),
KEY `dwd_sx_item_process_info_xfjbh` USING BTREE (`sxbh`)

) ENGINE = InnoDB DEFAULT CHARSET = utf8mb4 COMMENT '事项事项办理记录表'  ;

CREATE TABLE `test_data_exchange_sx_attach` (
`id` bigint(20) NOT NULL COMMENT '主键',
`sxbh` varchar(64) DEFAULT NULL COMMENT '事项件编号',
`link` text COMMENT '附件地址',
`name` varchar(500) DEFAULT NULL COMMENT '附件名称',
`original_name` varchar(500) DEFAULT NULL COMMENT '附件原名',
`extension` varchar(12) DEFAULT NULL COMMENT '附件拓展名',
`attach_size` bigint(20) DEFAULT NULL COMMENT '附件大小',
`create_time` datetime DEFAULT NULL COMMENT '创建时间',
`full_path` text COMMENT '文件完整路径',
`timestamp` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '抽取增量时间戳',
PRIMARY KEY (`id`),
UNIQUE KEY `visit_attach_pkey` USING BTREE (`id`),
KEY `auto_shard_key_id` USING BTREE (`id`),
KEY `index_update_time` (`update_time`)
) ENGINE = InnoDB DEFAULT CHARSET = utf8mb4 COMMENT '附件表';





