jQuery(document).ready(function($) {
    // 初始化日期选择器
    $('.date-picker').datepicker({
        dateFormat: 'yy-mm-dd'
    });
    
    // 加载初始交易数据
    loadTransactions();
    
    // 表单提交处理
    $('#fortunepay-transaction-filter').on('submit', function(e) {
        e.preventDefault();
        loadTransactions();
    });
    
    // 交易加载函数
    function loadTransactions() {
        const container = $('#fortunepay-transactions-container');
        container.html('<div class="loading-overlay"><div class="spinner"></div><p>' + fortunepay_admin_params.loading_text + '</p></div>');
        
        const data = {
            action: 'fortunepay_get_transactions',
            nonce: fortunepay_admin_params.nonce,
            date_from: $('#fortunepay-date-from').val(),
            date_to: $('#fortunepay-date-to').val(),
            phone: $('#fortunepay-phone').val(),
            ref: $('#fortunepay-ref').val(),
            txn_id: $('#fortunepay-txn-id').val()
        };
        
        $.post(fortunepay_admin_params.ajax_url, data, function(response) {
            if (response.success) {
                container.html(response.data.html);
            } else {
                container.html('<div class="error notice"><p>' + response.data.message + '</p></div>');
            }
        }).fail(function() {
            container.html('<div class="error notice"><p>' + fortunepay_admin_params.loading_error + '</p></div>');
        });
    }
    
    // 添加AJAX处理函数获取交易数据
    // 注意：此函数需要在PHP端实现
});