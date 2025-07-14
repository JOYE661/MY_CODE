<?php
class Fortune_Pay_API {
    private $test_mode;
    private $merchant_secret;
    private $merchant_key;
    private $preset_id;
    private $ip_whitelist;
    
    public function __construct($test_mode, $merchant_secret, $merchant_key, $preset_id, $ip_whitelist) {
        $this->test_mode = $test_mode;// 测试模式标志
        $this->merchant_secret = $merchant_secret;// 商户密钥
        $this->merchant_key = $merchant_key;// 商户API密钥
        $this->preset_id = $preset_id;// 预设ID
        $this->ip_whitelist = $ip_whitelist;// IP白名单
    }
    
    // 生成支付链接（对应文档中的/payment/generate接口）
    public function generate_payment_link($params) {
        $api_domain = $this->test_mode 
            ? FORTUNE_PAY_API_TEST_DOMAIN 
            : FORTUNE_PAY_API_PROD_DOMAIN;
            
        $api_path = '/payment/generate';
        
        // 确保必要参数存在
        if (!isset($params['merchant_key'])) {
            $params['merchant_key'] = $this->merchant_key;
        }
        
        if (!isset($params['preset'])) {
            $params['preset'] = $this->preset_id;
        }
        
        $params['merchant_secret'] = $this->merchant_secret;
        $query_string = http_build_query($params);
        $api_url = "{$api_domain}{$api_path}?{$query_string}";
        
        // 记录API请求
        $this->log('API请求: ' . $api_url);
        
        // 发送请求并返回结果
        $response = wp_remote_get($api_url, array(
            'timeout' => 30,
            'headers' => array(
                'Content-Type' => 'application/x-www-form-urlencoded',
                'Accept' => 'application/json',
                'Authorization' => 'Bearer ' . $this->merchant_secret
            )
        ));

        if (is_wp_error($response)) {
            $error_message = $response->get_error_message();
            $this->log('API请求错误: ' . $error_message);
            return array(
                'status' => 'error',
                'message' => 'API request failed: ' . $error_message
            );
        }

        $response_code = wp_remote_retrieve_response_code($response);
        $body = wp_remote_retrieve_body($response);
        
        if ($response_code !== 200) {
            $this->log('API响应状态码错误: ' . $response_code . ', 响应内容: ' . $body);
            return array(
                'status' => 'error',
                'message' => 'API response error with status code: ' . $response_code
            );
        }

        $data = json_decode($body, true);
        if (json_last_error() !== JSON_ERROR_NONE) {
            $this->log('无效的JSON响应: ' . $body);
            return array(
                'status' => 'error',
                'message' => 'Invalid JSON response'
            );
        }

        if (empty($data)) {
            $this->log('空的API响应: ' . $body);
            return array(
                'status' => 'error',
                'message' => 'Empty API response'
            );
        }

        $this->log('API响应数据: ' . print_r($data, true));
        return $data;
    }
    
    // 查询交易状态（对应文档中的/payment/status接口）
    public function get_transaction_status($ref) {
        $api_domain = $this->test_mode 
            ? FORTUNE_PAY_API_TEST_DOMAIN 
            : FORTUNE_PAY_API_PROD_DOMAIN;
            
        $api_path = '/payment/status';
        
        $params = [
            'merchant_key' => $this->merchant_key,
            'ref' => $ref,
            'merchant_secret' => $this->merchant_secret
        ];
        
        $query_string = http_build_query($params);
        $api_url = "{$api_domain}{$api_path}?{$query_string}";
        
        $this->log('查询交易状态: ' . $api_url);
        
        $response = wp_remote_get($api_url, array(
            'timeout' => 30,
            'headers' => array(
                'Content-Type' => 'application/x-www-form-urlencoded',
                'Accept' => 'application/json',
                'Authorization' => 'Bearer ' . $this->merchant_secret
            )
        ));

        if (is_wp_error($response)) {
            $error_message = $response->get_error_message();
            $this->log('查询交易状态请求错误: ' . $error_message);
            return array(
                'status' => 'error',
                'message' => 'Transaction status request failed: ' . $error_message
            );
        }

        $response_code = wp_remote_retrieve_response_code($response);
        $body = wp_remote_retrieve_body($response);
        
        if ($response_code !== 200) {
            $this->log('交易状态API响应状态码错误: ' . $response_code . ', 响应内容: ' . $body);
            return array(
                'status' => 'error',
                'message' => 'Transaction status API response error with status code: ' . $response_code
            );
        }

        $data = json_decode($body, true);
        if (json_last_error() !== JSON_ERROR_NONE) {
            $this->log('无效的交易状态JSON响应: ' . $body);
            return array(
                'status' => 'error',
                'message' => 'Invalid transaction status JSON response'
            );
        }

        if (empty($data)) {
            $this->log('空的交易状态API响应: ' . $body);
            return array(
                'status' => 'error',
                'message' => 'Empty transaction status API response'
            );
        }

        return $data;
    }
    
    // 退款接口
    public function refund_payment($ref, $amount) {
        $api_domain = $this->test_mode 
            ? FORTUNE_PAY_API_TEST_DOMAIN 
            : FORTUNE_PAY_API_PROD_DOMAIN;
        
        $api_path = '/payment/refund'; // 假设退款接口路径为 /payment/refund
        
        $params = [
            'merchant_key' => $this->merchant_key,
            'ref' => $ref,
            'amount' => $amount,
            'merchant_secret' => $this->merchant_secret
        ];
        
        $api_url = "{$api_domain}{$api_path}";
        
        $this->log('退款请求: ' . $api_url . ' with params: ' . print_r($params, true));
        
        $response = wp_remote_post($api_url, array(
            'timeout' => 30,
            'body' => $params,
            'headers' => array(
                'Content-Type' => 'application/x-www-form-urlencoded',
                'Accept' => 'application/json',
                'Authorization' => 'Bearer ' . $this->merchant_secret
            )
        ));

        if (is_wp_error($response)) {
            $error_message = $response->get_error_message();
            $this->log('退款请求错误: ' . $error_message);
            return array(
                'status' => 'error',
                'message' => 'Refund request failed: ' . $error_message
            );
        }

        $response_code = wp_remote_retrieve_response_code($response);
        $body = wp_remote_retrieve_body($response);
        
        if ($response_code !== 200) {
            $this->log('退款API响应状态码错误: ' . $response_code . ', 响应内容: ' . $body);
            return array(
                'status' => 'error',
                'message' => 'Refund API response error with status code: ' . $response_code
            );
        }

        $data = json_decode($body, true);
        if (json_last_error() !== JSON_ERROR_NONE) {
            $this->log('无效的退款JSON响应: ' . $body);
            return array(
                'status' => 'error',
                'message' => 'Invalid refund JSON response'
            );
        }

        if (empty($data)) {
            $this->log('空的退款API响应: ' . $body);
            return array(
                'status' => 'error',
                'message' => 'Empty refund API response'
            );
        }

        return $data;
    }

    // 验证回调签名（使用文档中的SHA256算法）
    public function validate_callback_signature($txn_id, $ex_ref, $status, $processor, $amount, $signature) {
        $expected_signature = hash('sha256', "{$txn_id}:{$ex_ref}:{$status}:{$processor}:{$amount}:{$this->merchant_secret}");
        
        $this->log('验证签名: 预期签名 ' . $expected_signature . ' vs 实际签名 ' . $signature);
        
        return $signature === $expected_signature;
    }
    
    // 记录日志
    private function log($message) {
        if (!class_exists('WC_Logger')) {
            return;
        }
        
        $logger = wc_get_logger();
        $logger->debug($message, array('source' => 'fortune-pay-api'));
    }
}