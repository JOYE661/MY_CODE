<?php
class Fortune_Pay_Gateway extends WC_Payment_Gateway {//继承WC_Payment_Gateway类，实现自定义支付网关

    public function __construct() {//构造函数，初始化支付网关
        $this->id = 'fortune_pay';//支付网关ID
        $this->icon = apply_filters('woocommerce_fortune_pay_icon', ''); // 可设置支付图标
        $this->method_title = __('Fortune Pay', 'fortune-pay-gateway');//支付网关名称
        $this->method_description = __('通过Fortune Pay支付网关完成支付', 'fortune-pay-gateway');//支付网关描述
        $this->has_fields = false;//是否显示支付表单

        // 支持的功能
        $this->supports = array(
            'products',//支持产品
            'refunds',//支持退款
            'tokenization'//支持令牌化
        );

        // 初始化设置
        $this->init_form_fields();//初始化设置字段
        $this->init_settings();//初始化设置

        // 获取设置值
        $this->title = $this->get_option('title');//获取设置值
        $this->description = $this->get_option('description');//获取设置值
        $this->test_mode = 'yes' === $this->get_option('test_mode');//获取设置值
        $this->merchant_key = $this->get_option('merchant_key');//获取设置值
        $this->merchant_secret = $this->get_option('merchant_secret');//获取设置值
        $this->preset_id = $this->get_option('preset_id');//获取设置值
        $this->redirect_url = $this->get_option('redirect_url', home_url('/thank-you/'));//获取设置值
        $this->ip_whitelist = $this->get_option('ip_whitelist');//获取设置值

        // 动作钩子
        add_action('woocommerce_update_options_payment_gateways_' . $this->id, array($this, 'process_admin_options'));//更新支付网关选项
        add_action('woocommerce_thankyou_' . $this->id, array($this, 'thankyou_page'));//感谢页面显示交易信息
        add_action('woocommerce_before_checkout_form', array($this, 'display_payment_message'));//显示支付提示信息
    }

    // 初始化设置字段
    public function init_form_fields() {
        $this->form_fields = array(//初始化设置字段
            'enabled' => array(//启用/禁用
                'title' => __('启用/禁用', 'fortune-pay-gateway'),//标题
                'type' => 'checkbox',
                'label' => __('启用Fortune Pay支付网关', 'fortune-pay-gateway'),//标签
                'default' => 'no'//默认值
            ),
            'title' => array(//结账页面显示名称
                'title' => __('结账页面显示名称', 'fortune-pay-gateway'),//标题
                'type' => 'text',//类型
                'default' => __('Fortune Pay', 'fortune-pay-gateway'),//默认值
                'description' => __('用户在结账时看到的支付方式名称')//描述
            ),
            'description' => array(//结账页面描述
                'title' => __('结账页面描述', 'fortune-pay-gateway'),//标题
                'type' => 'textarea',//类型
                'default' => __('通过Fortune Pay钱包或其他支付方式完成支付', 'fortune-pay-gateway'),//默认值
                'description' => __('用户在结账时看到的支付方式描述')//描述
            ),
            'test_mode' => array(//测试模式
                'title' => __('测试模式', 'fortune-pay-gateway'),//标题
                'type' => 'checkbox',
                'label' => __('启用测试环境（使用测试API）', 'fortune-pay-gateway'),//标签
                'default' => 'yes'//默认值
            ),
            'merchant_key' => array(//商户密钥
                'title' => __('商户密钥 (Merchant Key)', 'fortune-pay-gateway'),//标题
                'type' => 'text',//类型
                'description' => __('在Fortune Pay门户设置中获取', 'fortune-pay-gateway'),//描述
                'desc_tip' => true//描述提示
            ),
            'merchant_secret' => array(//商户密钥
                'title' => __('商户密钥 (Merchant Secret)', 'fortune-pay-gateway'),//标题
                'type' => 'password',//类型
                'description' => __('在Fortune Pay门户设置中获取', 'fortune-pay-gateway'),//描述
                'desc_tip' => true//描述提示
            ),
            'preset_id' => array(//支付预设ID
                'title' => __('支付预设ID (Preset ID)', 'fortune-pay-gateway'),//标题
                'type' => 'text',
                'description' => __('在Fortune Pay门户创建的支付预设唯一ID', 'fortune-pay-gateway'),
                'desc_tip' => true//描述提示
            ),
            'redirect_url' => array(//支付完成重定向URL
                'title' => __('支付完成重定向URL', 'fortune-pay-gateway'),//标题
                'type' => 'text',
                'default' => home_url('/thank-you/'),
                'description' => __('需在Fortune Pay门户中设置为白名单URL', 'fortune-pay-gateway'),
                'desc_tip' => true//描述提示
            ),
            'ip_whitelist' => array(//IP白名单
                'title' => __('IP白名单', 'fortune-pay-gateway'),//标题
                'type' => 'text',
                'description' => __('请将服务器IP提交给Fortune Pay添加到白名单（多个IP用逗号分隔）', 'fortune-pay-gateway'),
                'desc_tip' => true//描述提示
            )
        );
    }

    // 经典结账页面支付表单
    public function payment_fields() {
        if ($this->description) {//如果描述存在
            echo wpautop(wptexturize($this->description));//显示描述
        }
        
        // 测试模式提示
        if ($this->test_mode) {
            echo '<div class="fortune-pay-test-notice notice notice-warning">';//测试模式提示
            echo '<p>' . __('当前处于测试模式，支付不会产生实际费用', 'fortune-pay-gateway') . '</p>';//测试模式提示
            echo '</div>';
        }
    }

    // 处理经典结账支付
    public function process_payment($order_id) {
        $order = wc_get_order($order_id);//获取订单
        if (!$order) {//如果订单不存在
            wc_add_notice(__('无效的订单', 'fortune-pay-gateway'), 'error');//显示错误信息
            return array('result' => 'fail');//返回失败
        }
        
        // 记录调试信息
        $this->log('开始处理订单 #' . $order_id);//记录调试信息
        
        // 验证必要的设置
        if (empty($this->merchant_key)) {
            $this->log('错误: 未配置merchant_key');//记录调试信息
            wc_add_notice(__('支付网关配置不完整，请联系管理员', 'fortune-pay-gateway'), 'error');//显示错误信息
            return array('result' => 'fail');//返回失败
        }
        
        if (empty($this->preset_id)) {
            $this->log('错误: 未配置preset_id');//记录调试信息
            wc_add_notice(__('支付网关配置不完整，请联系管理员', 'fortune-pay-gateway'), 'error');//显示错误信息
            return array('result' => 'fail');//返回失败
        }
        
        $api = $this->get_api_instance();//获取API实例
        
        // 生成外部参考号
        $external_ref = 'WC-' . $order->get_order_number() . '-' . time();//生成外部参考号
        
        // 准备API参数
        $params = array(
            'merchant_key' => $this->merchant_key,//商户密钥
            'preset' => $this->preset_id,//支付预设ID
            'amount' => number_format($order->get_total(), 2, '.', ''),//订单金额
            'ref' => $external_ref,//外部参考号
            'customer' => $order->get_billing_phone(),//客户电话
            'email' => $order->get_billing_email(),//客户邮箱
            'return_url' => $this->redirect_url,//重定向URL
            'callback_url' => add_query_arg('wc-api', 'fortune_pay_callback', home_url('/'))//回调URL  
        );
        
        $this->log('API请求参数: ' . print_r($params, true));//记录调试信息
        
        try {
            // 调用生成支付链接API
            $response = $api->generate_payment_link($params);
            
            $this->log('API响应: ' . print_r($response, true));//记录调试信息
            
            if ($response && isset($response['status']) && $response['status'] === 'success' && !empty($response['url_link'])) {//如果响应成功
                // 更新订单状态
                $order->update_status('pending', __('等待Fortune Pay支付确认', 'fortune-pay-gateway'));//更新订单状态
                $order->add_meta_data('fortune_pay_external_ref', $external_ref);//添加外部参考号
                $order->save();//保存订单
                
                // 返回重定向URL
                return array(
                    'result' => 'success',
                    'redirect' => $response['url_link']//重定向URL
                );
            } else {
                // 错误处理
                $error_msg = __('生成支付链接失败，请稍后再试', 'fortune-pay-gateway');
                if (isset($response['message'])) {
                    $error_msg = $response['message'];
                    
                    // 特定错误处理
                    if (strpos($error_msg, '5001') !== false) {
                        $error_msg = __('IP地址未在白名单中，请联系Fortune Pay支持', 'fortune-pay-gateway');
                    } elseif (strpos($error_msg, '5002') !== false) {
                        $error_msg = __('无效的商户密钥，请检查配置', 'fortune-pay-gateway');
                    } elseif (strpos($error_msg, '5003') !== false) {
                        $error_msg = __('无效的支付预设ID，请检查配置', 'fortune-pay-gateway');
                    }
                }
                
                $this->log('API错误: ' . $error_msg);
                wc_add_notice($error_msg, 'error');//显示错误信息
                return array('result' => 'fail');//返回失败
            }
        } catch (Exception $e) {
            $this->log('异常错误: ' . $e->getMessage());//记录调试信息
            wc_add_notice(__('支付处理过程中发生异常，请稍后再试', 'fortune-pay-gateway'), 'error');//显示错误信息
            return array('result' => 'fail');//返回失败
        }
    }

    // 结账区块支付处理
    public function process_payment_for_block($order_id) {
        return $this->process_payment($order_id);
    }

    // 感谢页面显示交易信息
    public function thankyou_page($order_id) {
        $order = wc_get_order($order_id);//获取订单
        $txn_id = $order->get_meta('fortune_pay_txn_id');//获取交易ID

        if ($txn_id) {//如果交易ID存在
            echo '<div class="fortune-pay-txn-info">';//交易信息
            echo '<p>' . sprintf(__('Fortune Pay交易ID: %s', 'fortune-pay-gateway'), $txn_id) . '</p>';//交易ID
            echo '</div>';
        }
    }

    // 显示支付提示信息
    public function display_payment_message() {
        // 获取当前选择的支付方式
            $chosen_payment_method = WC()->session->get('chosen_payment_method');//获取当前选择的支付方式
        
        // 检查是否是Fortune Pay支付方式
        if (is_checkout() && !is_wc_endpoint_url() && $chosen_payment_method === 'fortune_pay') {//如果当前选择的支付方式是Fortune Pay支付方式
            echo '<div class="fortune-pay-message notice notice-info">';
            echo '<p>' . __('您将被重定向到Fortune Pay完成支付，支付成功后会自动返回商店', 'fortune-pay-gateway') . '</p>';
            
            // 测试模式提示
            if ($this->test_mode) {
                echo '<p class="test-mode-hint">' . __('测试模式: 请使用测试账号 09615050543 / 1234 / 123456', 'fortune-pay-gateway') . '</p>';
            }
            
            echo '</div>';
        }
    }

    // 获取API实例
    private function get_api_instance() {
        return new Fortune_Pay_API(
            $this->test_mode,
            $this->merchant_secret,
            $this->merchant_key,
            $this->preset_id,
            $this->ip_whitelist
        );
    }

    // 验证回调签名
    public function verify_callback_signature($data) {
        // 记录签名验证开始
        $this->log('开始验证回调签名');
        
        // 检查签名是否存在
        if (!isset($data['signature'])) {
            $this->log('错误：回调数据缺少signature字段');
            return false;
        }
        
        $signature = $data['signature'];
        $txn_id = isset($data['txn_id']) ? $data['txn_id'] : '';
        $ex_ref = isset($data['ex_ref']) ? $data['ex_ref'] : '';
        $status = isset($data['status']) ? $data['status'] : '';
        $processor = isset($data['processor']) ? $data['processor'] : '';
        $amount = isset($data['amount']) ? $data['amount'] : '0';
        
        // 初始化预期签名和日志信息
        $secret_key = $this->merchant_secret;
        $algorithm = 'sha256';
        $formatted_amount = number_format((float)$amount, 1, '.', '');
        $sign_str = "{$txn_id}:{$ex_ref}:{$status}:{$processor}:{$formatted_amount}:{$secret_key}";
        $signature_log = '支付网关API (SHA256)';
        
        // 生成预期签名
        $expected_signature = hash($algorithm, $sign_str);
        
        // 记录签名验证详情
        $this->log("{$signature_log} 签名验证");
        $this->log("签名拼接字符串: {$sign_str}");
        $this->log("使用算法: {$algorithm}");
        $this->log("使用密钥: " . (strlen($secret_key) > 10 ? substr($secret_key, 0, 10) . '...' : $secret_key));
        $this->log("预期签名: {$expected_signature}");
        $this->log("实际签名: {$signature}");
        
        // 验证签名并返回结果
        $is_valid = $signature === $expected_signature;
        if (!$is_valid) {
            $this->log('错误：签名验证失败');
        } else {
            $this->log('签名验证成功');
        }
        
        return $is_valid;
    }
    
    // 添加日志方法
    public function log($message) {
        if (is_array($message) || is_object($message)) {
            $message = print_r($message, true);
        }
        
        if (!class_exists('WC_Logger')) {
            return;
        }
        
        $logger = wc_get_logger();
        $logger->debug($message, array('source' => 'fortune-pay-gateway'));
    }

    // 处理退款
    public function process_refund($order_id, $amount = null, $reason = '') {
        $order = wc_get_order($order_id);
        if (!$order) {
            return false;
        }
        
        $external_ref = $order->get_meta('fortune_pay_external_ref');
        if (empty($external_ref)) {
            $this->log('错误: 未找到外部参考号');
            return false;
        }
        
        if (is_null($amount)) {
            $amount = $order->get_total();
        }
        
        $api = $this->get_api_instance();
        $response = $api->refund_payment($external_ref, $amount);
        
        $this->log('退款响应: ' . print_r($response, true));
        
        if ($response && isset($response['status']) && $response['status'] === 'success') {
            return true;
        } else {
            return false;
        }
    }
}