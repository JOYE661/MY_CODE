<?php
/**
 * Plugin Name: Fortune Pay for WooCommerce
 * Description: 集成Fortune Pay支付网关到WooCommerce商店，支持结账区块与经典结账流程
 * Version: 1.2.0
 * Author: Your Name
 * Author URI: https://yourwebsite.com
 * License: GPL-2.0+
 * Text Domain: fortune-pay-gateway
 * Domain Path: /languages
 */

// 防止直接访问
if (!defined('ABSPATH')) exit; 

// 定义插件常量
define('FORTUNE_PAY_VERSION', '1.2.0');
define('FORTUNE_PAY_PLUGIN_DIR', plugin_dir_path(__FILE__));
define('FORTUNE_PAY_PLUGIN_URL', plugin_dir_url(__FILE__));
define('FORTUNE_PAY_API_TEST_DOMAIN', 'https://fp-payment-gateway-v3.fortunepay.com.ph');
define('FORTUNE_PAY_API_PROD_DOMAIN', 'https://paymentgateway.fortunepay.com.ph');

// 检查WooCommerce是否安装
if (!in_array('woocommerce/woocommerce.php', apply_filters('active_plugins', get_option('active_plugins')))) {
    add_action('admin_notices', 'fortune_pay_missing_woocommerce_notice');
    return;
}

// 确保WooCommerce加载完成后再加载插件
add_action('woocommerce_loaded', function() {
    // 加载核心类
    require_once FORTUNE_PAY_PLUGIN_DIR . 'class-fortune-pay-gateway.php';
    require_once FORTUNE_PAY_PLUGIN_DIR . 'fortune-pay-api.php';

    // 注册支付网关
    add_filter('woocommerce_payment_gateways', 'fortune_pay_add_gateway');
    function fortune_pay_add_gateway($gateways) {
        $gateways[] = 'Fortune_Pay_Gateway';
        return $gateways;
    }
});

// 插件初始化
function fortune_pay_init() {
    // 加载翻译
    load_plugin_textdomain('fortune-pay-gateway', false, dirname(plugin_basename(__FILE__)) . '/languages');

    // 注册前端资源
    add_action('wp_enqueue_scripts', 'fortune_pay_enqueue_assets');

    // 注册AJAX处理器
    add_action('wp_ajax_fortune_pay_create_payment', 'fortune_pay_ajax_create_payment');
    add_action('wp_ajax_nopriv_fortune_pay_create_payment', 'fortune_pay_ajax_create_payment');

    // 回调路由
    add_action('woocommerce_api_fortune_pay_callback', 'fortune_pay_process_callback');
}
add_action('plugins_loaded', 'fortune_pay_init');

// 加载前端资源
function fortune_pay_enqueue_assets() {
    if (is_checkout()) {
        // CSS
        wp_enqueue_style(
            'fortune-pay-style',
            FORTUNE_PAY_PLUGIN_URL . 'assets/css/fortune-pay-style.css',
            array(),
            FORTUNE_PAY_VERSION
        );

        // JS
        wp_enqueue_script(
            'fortune-pay-script',
            FORTUNE_PAY_PLUGIN_URL . 'assets/js/fortune-pay-script.js',
            array('jquery'),
            FORTUNE_PAY_VERSION,
            true
        );

        // 本地化数据
        wp_localize_script('fortune-pay-script', 'fortunePay', array(
            'ajaxUrl' => admin_url('admin-ajax.php'),
            'nonce' => wp_create_nonce('fortune_pay_nonce'),
            'isBlockCheckout' => function_exists('is_checkout_block') && is_checkout_block(),
            'i18n' => array(
                'processing' => __('处理支付中...', 'fortune-pay-gateway'),
                'redirecting' => __('即将重定向到Fortune Pay...', 'fortune-pay-gateway'),
                'error' => __('支付处理失败，请重试', 'fortune-pay-gateway')
            )
        ));
    }
}

// WooCommerce未安装提示
function fortune_pay_missing_woocommerce_notice() {
    echo '<div class="error"><p>' . sprintf(
        __('Fortune Pay插件需要 %s 已安装并激活', 'fortune-pay-gateway'),
        '<a href="https://woocommerce.com/" target="_blank">WooCommerce</a>'
    ) . '</p></div>';
}

// AJAX创建支付处理函数
function fortune_pay_ajax_create_payment() {
    check_ajax_referer('fortune_pay_nonce', 'nonce');
    $order_id = isset($_POST['order_id']) ? intval($_POST['order_id']) : 0;
    if (!$order_id) {
        wp_send_json_error(array('message' => __('无效的订单ID', 'fortune-pay-gateway')));
    }
    
    $gateway = new Fortune_Pay_Gateway();
    $result = $gateway->process_payment($order_id);
    
    if ($result['result'] === 'success') {
        wp_send_json_success(array('redirect_url' => $result['redirect']));
    } else {
        wp_send_json_error(array('message' => __('支付处理失败，请重试', 'fortune-pay-gateway')));
    }
}

// 处理回调函数
function fortune_pay_process_callback() {
    $gateway = new Fortune_Pay_Gateway();
    
    // 获取回调数据
    $data = file_get_contents('php://input');
    $json_data = json_decode($data, true);
    
    // 记录回调数据
    $gateway->log('回调数据: ' . print_r($json_data, true));
    
    $order_id = null;
    if ($json_data && isset($json_data['ex_ref'])) {
        $ex_ref = $json_data['ex_ref'];
        $parts = explode('-', $ex_ref);
        if (count($parts) >= 2) {
            $order_id = intval($parts[1]);
        }
    }
    
    // 添加调试信息
    $gateway->log('解析出的订单ID: ' . $order_id);
    $gateway->log('支付状态: ' . (isset($json_data['status']) ? $json_data['status'] : '未知'));
    
    if ($order_id) {
        $order = wc_get_order($order_id);
        
        if ($order) {
            // 验证签名
            if ($gateway->verify_callback_signature($json_data)) {
                // 根据支付状态更新订单
                if (isset($json_data['status']) && $json_data['status'] === 'S') { 
                    // 支付成功，将订单状态更新为正在处理
                    $order->update_status('processing', __('Fortune Pay支付已完成', 'fortune-pay-gateway'));
                    $order->add_meta_data('fortune_pay_txn_id', isset($json_data['txn_id']) ? $json_data['txn_id'] : 'N/A');
                    $order->save();
                    
                    // 发送支付成功邮件
                    WC()->mailer()->get_emails()['WC_Email_Customer_Processing_Order']->trigger($order_id);
                    
                    // 返回成功响应
                    wp_send_json_success(array('status' => 'success', 'message' => 'Order updated successfully'));
                } else {
                    // 支付失败
                    $order->update_status('failed', __('Fortune Pay支付失败', 'fortune-pay-gateway'));
                    wp_send_json_error(array('status' => 'error', 'message' => 'Payment failed'));
                }
            } else {
                // 签名验证失败
                $gateway->log('签名验证失败: ' . print_r($json_data, true));
                wp_send_json_error(array('status' => 'error', 'message' => 'Invalid signature'));
            }
        } else {
            // 订单不存在
            wp_send_json_error(array('status' => 'error', 'message' => 'Order not found'));
        }
    } else {
        // 无效的回调数据
        wp_send_json_error(array('status' => 'error', 'message' => 'Invalid callback data'));
    }
    
    wp_die();
}