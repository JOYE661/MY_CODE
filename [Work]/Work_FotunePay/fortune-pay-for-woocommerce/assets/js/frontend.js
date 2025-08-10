jQuery(document).ready(function($) {
    // 手机号验证逻辑
    $('#fortunepay_phone').on('input', function() {
        const phone = $(this).val().trim();
        const resultContainer = $('#fortunepay-validation-result');
        
        // 清除之前的验证状态
        resultContainer.removeClass('valid invalid error').text('');
        
        // 验证格式
        if (!phone.match(/^[0-9]{10}$/)) {
            if (phone.length > 0) {
                resultContainer.addClass('invalid').text(fortunepay_params.invalid_number);
            }
            return;
        }
        
        // 显示加载状态
        resultContainer.addClass('checking').text(fortunepay_params.checking_text);
        
        // 发送AJAX请求验证用户
        $.ajax({
            url: fortunepay_params.ajax_url,
            type: 'POST',
            data: {
                action: 'fortunepay_check_user',
                phone: phone
            },
            success: function(response) {
                if (response.success) {
                    if (response.data.exists) {
                        resultContainer.removeClass('checking invalid').addClass('valid').text(response.data.message);
                    } else {
                        resultContainer.removeClass('checking').addClass('invalid').text(response.data.message);
                    }
                } else {
                    resultContainer.removeClass('checking').addClass('error').text(fortunepay_params.api_error);
                }
            },
            error: function() {
                resultContainer.removeClass('checking').addClass('error').text(fortunepay_params.api_error);
            }
        });
    });
    
    // 结账表单提交前的额外验证
    $('form.checkout').on('checkout_place_order', function() {
        if ($('#payment_method_fortunepay').is(':checked')) {
            const resultContainer = $('#fortunepay-validation-result');
            
            if (resultContainer.hasClass('invalid') || resultContainer.hasClass('error')) {
                alert(fortunepay_params.user_invalid);
                return false;
            }
            
            if (!resultContainer.hasClass('valid')) {
                alert(fortunepay_params.invalid_number);
                return false;
            }
        }
        return true;
    });
});