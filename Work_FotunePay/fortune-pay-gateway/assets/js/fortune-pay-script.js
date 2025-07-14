// Fortune Pay支付网关前端脚本
jQuery(document).ready(function($) {
    // 经典结账支付按钮处理
    if (!fortunePay.isBlockCheckout) {
        $('#place_order').click(function(e) {
            if ($('input[name="payment_method"]:checked').val() === 'fortune_pay') {
                e.preventDefault();
                processFortunePayPayment();
            }
        });
    }
    
    // 处理Fortune Pay支付
    function processFortunePayPayment() {
        const orderId = $('input[name="order_id"]').val();
        if (!orderId) {
            alert(fortunePay.i18n.error);
            return;
        }
        
        showPaymentModal();
        
        $.ajax({
            url: fortunePay.ajaxUrl,
            type: 'POST',
            data: {
                action: 'fortune_pay_create_payment',
                order_id: orderId,
                nonce: fortunePay.nonce
            },
            success: function(response) {
                hidePaymentModal();
                if (response.success && response.data.redirect_url) {
                    window.location.href = response.data.redirect_url;
                } else {
                    alert(response.data.message || fortunePay.i18n.error);
                }
            },
            error: function() {
                hidePaymentModal();
                alert(fortunePay.i18n.error);
            }
        });
    }
    
    // AJAX创建支付链接
    $(document).on('click', '.wp-block-woocommerce-checkout-place-order-button', function(e) {
        if ($('input[name="payment_method"]:checked').val() === 'fortune_pay') {
            e.preventDefault();
            const orderId = $(this).data('order-id');
            if (orderId) {
                processFortunePayPayment();
            }
        }
    });
    
    // 显示支付模态框
    function showPaymentModal() {
        const modal = `
            <div class="fortune-pay-modal active">
                <div class="fortune-pay-modal-content">
                    <div class="fortune-pay-spinner"></div>
                    <p>${fortunePay.i18n.processing}</p>
                    <p>${fortunePay.i18n.redirecting}</p>
                </div>
            </div>
        `;
        $('body').append(modal);
    }
    
    // 隐藏支付模态框
    function hidePaymentModal() {
        $('.fortune-pay-modal').remove();
    }
});