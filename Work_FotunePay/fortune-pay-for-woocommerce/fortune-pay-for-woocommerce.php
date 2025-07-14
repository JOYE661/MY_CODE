<?php
/**
 * Plugin Name: FortunePay for WooCommerce
 * Plugin URI: https://yourdomain.com/
 * Description: FortunePay现金提现支付网关集成
 * Version: 1.0.0
 * Author: Your Name
 * Author URI: https://yourdomain.com/
 * License: GPL-3.0+
 * License URI: http://www.gnu.org/licenses/gpl-3.0.html
 * Text Domain: fortunepay
 * Domain Path: /languages
 */

if (!defined('ABSPATH')) {
    exit; // Exit if accessed directly
}

// 确保WooCommerce已激活
add_action('plugins_loaded', 'init_fortunepay_gateway', 0);

function init_fortunepay_gateway() {
    if (!class_exists('WC_Payment_Gateway')) {
        return;
    }

    class WC_Gateway_FortunePay extends WC_Payment_Gateway {
        public function __construct() {
            $this->id = 'fortunepay';
            $this->icon = plugins_url('assets/fortune-logo.png', __FILE__);
            $this->has_fields = true;
            $this->method_title = __('FortunePay', 'fortunepay');
            $this->method_description = __('通过FortunePay钱包进行现金提现支付', 'fortunepay');
            
            $this->init_form_fields();
            $this->init_settings();
            
            $this->title = $this->get_option('title');
            $this->description = $this->get_option('description');
            $this->enabled = $this->get_option('enabled');
            $this->testmode = 'yes' === $this->get_option('testmode');
            $this->client_id = $this->testmode ? $this->get_option('test_client_id') : $this->get_option('client_id');
            $this->client_secret = $this->testmode ? $this->get_option('test_client_secret') : $this->get_option('client_secret');
            $this->client_signature_key = $this->testmode ? $this->get_option('test_client_signature_key') : $this->get_option('client_signature_key');
            
            $this->base_url = $this->testmode 
                ? 'https://devuserservice.fortunepay.com.ph' 
                : 'https://produserservice.fortunepay.com.ph';
            
            add_action('woocommerce_update_options_payment_gateways_' . $this->id, array($this, 'process_admin_options'));
            add_action('woocommerce_thankyou_' . $this->id, array($this, 'thankyou_page'));
            add_action('woocommerce_admin_order_data_after_billing_address', array($this, 'display_admin_order_meta'), 10, 1);
            add_filter('woocommerce_order_data_store_cpt_get_orders_query', array($this, 'handle_custom_query_var'), 10, 2);
        }
        
        public function init_form_fields() {
            $this->form_fields = array(
                'enabled' => array(
                    'title'       => __('启用/禁用', 'fortunepay'),
                    'label'       => __('启用FortunePay支付', 'fortunepay'),
                    'type'        => 'checkbox',
                    'description' => '',
                    'default'     => 'no'
                ),
                'title' => array(
                    'title'       => __('标题', 'fortunepay'),
                    'type'        => 'text',
                    'description' => __('用户支付时看到的支付方式名称', 'fortunepay'),
                    'default'     => __('FortunePay钱包支付', 'fortunepay'),
                    'desc_tip'    => true,
                ),
                'description' => array(
                    'title'       => __('描述', 'fortunepay'),
                    'type'        => 'textarea',
                    'description' => __('支付方式描述，用户支付时可见', 'fortunepay'),
                    'default'     => __('使用FortunePay钱包支付，需要验证您的手机号', 'fortunepay'),
                    'desc_tip'    => true,
                ),
                'testmode' => array(
                    'title'       => __('测试模式', 'fortunepay'),
                    'label'       => __('启用测试模式', 'fortunepay'),
                    'type'        => 'checkbox',
                    'description' => __('测试模式使用FortunePay的测试环境', 'fortunepay'),
                    'default'     => 'yes',
                    'desc_tip'    => true,
                ),
                'test_client_id' => array(
                    'title'       => __('测试环境 Client ID', 'fortunepay'),
                    'type'        => 'text',
                    'description' => __('FortunePay测试环境提供的Client ID', 'fortunepay'),
                    'default'     => '',
                ),
                'test_client_secret' => array(
                    'title'       => __('测试环境 Client Secret', 'fortunepay'),
                    'type'        => 'password',
                    'description' => __('FortunePay测试环境提供的Client Secret', 'fortunepay'),
                    'default'     => '',
                ),
                'test_client_signature_key' => array(
                    'title'       => __('测试环境 Signature Key', 'fortunepay'),
                    'type'        => 'password',
                    'description' => __('FortunePay测试环境提供的签名密钥', 'fortunepay'),
                    'default'     => '',
                ),
                'client_id' => array(
                    'title'       => __('生产环境 Client ID', 'fortunepay'),
                    'type'        => 'text',
                    'description' => __('FortunePay生产环境提供的Client ID', 'fortunepay'),
                    'default'     => '',
                ),
                'client_secret' => array(
                    'title'       => __('生产环境 Client Secret', 'fortunepay'),
                    'type'        => 'password',
                    'description' => __('FortunePay生产环境提供的Client Secret', 'fortunepay'),
                    'default'     => '',
                ),
                'client_signature_key' => array(
                    'title'       => __('生产环境 Signature Key', 'fortunepay'),
                    'type'        => 'password',
                    'description' => __('FortunePay生产环境提供的签名密钥', 'fortunepay'),
                    'default'     => '',
                ),
                'min_amount' => array(
                    'title'       => __('最低支付金额', 'fortunepay'),
                    'type'        => 'number',
                    'description' => __('FortunePay要求的最低支付金额 (PHP)', 'fortunepay'),
                    'default'     => 100,
                    'custom_attributes' => array(
                        'min'  => 100,
                        'step' => 'any',
                    ),
                ),
                'max_amount' => array(
                    'title'       => __('最高支付金额', 'fortunepay'),
                    'type'        => 'number',
                    'description' => __('FortunePay要求的最高支付金额 (PHP)', 'fortunepay'),
                    'default'     => 50000,
                    'custom_attributes' => array(
                        'min'  => 100,
                        'step' => 'any',
                    ),
                ),
            );
        }
        
        public function payment_fields() {
            if ($this->description) {
                echo wpautop(wptexturize($this->description));
            }
            
            woocommerce_form_field('fortunepay_phone', array(
                'type'        => 'tel',
                'label'       => __('FortunePay手机号码', 'fortunepay'),
                'class'       => array('form-row-wide'),
                'required'    => true,
                'placeholder' => __('请输入10位手机号码', 'fortunepay'),
                'input_class' => array('input-text'),
                'custom_attributes' => array(
                    'pattern' => '[0-9]{10}',
                    'maxlength' => 10,
                    'minlength' => 10,
                ),
            ));
        }
        
        public function validate_fields() {
            if (empty($_POST['fortunepay_phone'])) {
                wc_add_notice(__('请输入您的FortunePay手机号码', 'fortunepay'), 'error');
                return false;
            }
            
            $phone = wc_clean($_POST['fortunepay_phone']);
            
            if (!preg_match('/^[0-9]{10}$/', $phone)) {
                wc_add_notice(__('手机号码必须是10位数字', 'fortunepay'), 'error');
                return false;
            }
            
            // 检查用户是否存在
            $response = $this->check_user_exists($phone);
            
            if (is_wp_error($response)) {
                wc_add_notice(__('无法验证您的账户，请稍后再试', 'fortunepay'), 'error');
                return false;
            }
            
            if (isset($response['user_exist']) && $response['user_exist']) {
                return true;
            } else {
                wc_add_notice(__('该手机号不是FortunePay注册用户', 'fortunepay'), 'error');
                return false;
            }
        }
        
        private function check_user_exists($phone) {
            $url = $this->base_url . '/api/external/v1/cashout/checkuser?customer_number=' . $phone;
            
            $args = array(
                'headers' => array(
                    'Content-Type'  => 'application/json',
                    'client-id'     => $this->client_id,
                    'client-secret' => $this->client_secret,
                ),
                'timeout' => 30,
            );
            
            $response = wp_remote_get($url, $args);
            
            if (is_wp_error($response)) {
                return $response;
            }
            
            $body = wp_remote_retrieve_body($response);
            $data = json_decode($body, true);
            
            if ($response['response']['code'] == 200) {
                return $data['data'];
            } else {
                return new WP_Error('api_error', $data['message'] ?? __('API请求失败', 'fortunepay'));
            }
        }
        
        public function process_payment($order_id) {
            $order = wc_get_order($order_id);
            
            // 检查金额限制
            $total = $order->get_total();
            $min = $this->get_option('min_amount', 100);
            $max = $this->get_option('max_amount', 50000);
            
            if ($total < $min || $total > $max) {
                wc_add_notice(sprintf(
                    __('支付金额必须在 %s 至 %s PHP之间', 'fortunepay'),
                    wc_price($min),
                    wc_price($max)
                ), 'error');
                return false;
            }
            
            $phone = wc_clean($_POST['fortunepay_phone']);
            
            // 执行现金提现
            $response = $this->process_cashout($order, $phone);
            
            if (is_wp_error($response)) {
                wc_add_notice($response->get_error_message(), 'error');
                return false;
            }
            
            // 保存交易信息
            $order->update_meta_data('_fortunepay_reference_code', $response['reference_code']);
            $order->update_meta_data('_fortunepay_external_ref_code', $response['external_reference_code']);
            $order->update_meta_data('_fortunepay_customer_number', $phone);
            $order->update_meta_data('_fortunepay_signature', $response['signature']);
            $order->update_meta_data('_fortunepay_txn_id', $response['txn_id'] ?? '');
            
            // 标记订单为处理中
            $order->update_status('processing', __('FortunePay支付处理中', 'fortunepay'));
            
            // 清空购物车
            WC()->cart->empty_cart();
            
            return array(
                'result'   => 'success',
                'redirect' => $this->get_return_url($order)
            );
        }
        
        private function process_cashout($order, $phone) {
            $url = $this->base_url . '/api/external/v1/cashout/process';
            
            $body = array(
                'customer_number'     => $phone,
                'external_ref_code'   => $order->get_order_number(),
                'external_site'       => get_site_url(),
                'amount'              => number_format($order->get_total(), 2, '.', ''),
                'external_username'   => $order->get_billing_first_name() . ' ' . $order->get_billing_last_name(),
            );
            
            $args = array(
                'body'    => json_encode($body),
                'headers' => array(
                    'Content-Type'  => 'application/json',
                    'client-id'     => $this->client_id,
                    'client-secret' => $this->client_secret,
                ),
                'timeout' => 45,
            );
            
            $response = wp_remote_post($url, $args);
            
            if (is_wp_error($response)) {
                return $response;
            }
            
            $body = wp_remote_retrieve_body($response);
            $data = json_decode($body, true);
            
            if ($response['response']['code'] == 200) {
                return $data['data'];
            } else {
                $message = $data['message'] ?? __('API请求失败', 'fortunepay');
                $code = $data['code'] ?? $response['response']['code'];
                return new WP_Error('api_error', "[{$code}] {$message}");
            }
        }
        
        public function thankyou_page($order_id) {
            $order = wc_get_order($order_id);
            $reference = $order->get_meta('_fortunepay_reference_code');
            
            if ($reference) {
                echo '<div class="fortune-thankyou">';
                echo '<h3>' . __('FortunePay支付信息', 'fortunepay') . '</h3>';
                echo '<p><strong>' . __('交易参考号:', 'fortunepay') . '</strong> ' . esc_html($reference) . '</p>';
                echo '<p><strong>' . __('手机号码:', 'fortunepay') . '</strong> ' . esc_html($order->get_meta('_fortunepay_customer_number')) . '</p>';
                echo '<p><strong>' . __('交易金额:', 'fortunepay') . '</strong> ' . wc_price($order->get_total()) . '</p>';
                echo '</div>';
            }
        }
        
        public function display_admin_order_meta($order) {
            if ($order->get_payment_method() !== 'fortunepay') {
                return;
            }
            
            $txn_id = $order->get_meta('_fortunepay_txn_id');
            $ref_code = $order->get_meta('_fortunepay_reference_code');
            $customer_number = $order->get_meta('_fortunepay_customer_number');
            $signature = $order->get_meta('_fortunepay_signature');
            $valid = $order->get_meta('_fortunepay_signature_valid');
            
            echo '<div class="fortune-order-details">';
            echo '<h3>' . __('FortunePay交易详情', 'fortunepay') . '</h3>';
            echo '<p><strong>' . __('交易ID:', 'fortunepay') . '</strong> ' . ($txn_id ? esc_html($txn_id) : __('未获取', 'fortunepay')) . '</p>';
            echo '<p><strong>' . __('参考号:', 'fortunepay') . '</strong> ' . ($ref_code ? esc_html($ref_code) : __('未获取', 'fortunepay')) . '</p>';
            echo '<p><strong>' . __('客户手机号:', 'fortunepay') . '</strong> ' . esc_html($customer_number) . '</p>';
            
            if ($signature && $txn_id && $order->get_total()) {
                $is_valid = $this->validate_signature(
                    $txn_id,
                    $order->get_meta('_fortunepay_external_ref_code'),
                    $customer_number,
                    $order->get_total(),
                    $signature
                );
                
                echo '<p><strong>' . __('签名状态:', 'fortunepay') . '</strong> ';
                echo $is_valid 
                    ? '<span style="color:green">' . __('有效', 'fortunepay') . '</span>' 
                    : '<span style="color:red">' . __('无效', 'fortunepay') . '</span>';
                echo '</p>';
                
                // 保存验证结果
                $order->update_meta_data('_fortunepay_signature_valid', $is_valid);
                $order->save();
            }
            
            echo '</div>';
        }
        
        private function validate_signature($txn_id, $external_ref, $customer_number, $amount, $signature) {
            $signature_data = sprintf(
                '%s:%s:%s:%s:%s',
                $txn_id,
                $external_ref,
                $customer_number,
                number_format($amount, 2, '.', ''),
                $this->client_signature_key
            );
            
            $calculated_signature = sha1($signature_data);
            
            return hash_equals($calculated_signature, $signature);
        }
        
        public function handle_custom_query_var($query, $query_vars) {
            if (!empty($query_vars['fortunepay_ref'])) {
                $query['meta_query'][] = array(
                    'key' => '_fortunepay_reference_code',
                    'value' => esc_attr($query_vars['fortunepay_ref']),
                );
            }
            
            return $query;
        }
    }
    
    // 添加支付网关到WooCommerce
    function add_fortunepay_gateway($methods) {
        $methods[] = 'WC_Gateway_FortunePay';
        return $methods;
    }
    add_filter('woocommerce_payment_gateways', 'add_fortunepay_gateway');
}

// 加载语言文件
function fortunepay_load_textdomain() {
    load_plugin_textdomain('fortunepay', false, dirname(plugin_basename(__FILE__)) . '/languages/');
}
add_action('plugins_loaded', 'fortunepay_load_textdomain');