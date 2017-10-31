jQuery(function($) {
    $('.static, .field label').click(function() {
        p = $(this).parent()
        p.children('.edit').show()
        p.children('.static').hide()
    });
    $('input.revert').click(function() {
        p = $(this).parent()
        p.children('.edit').hide()
        p.children('.static').show()
        p.children('.edit.value').attr('value', $(this).next('.static').text())
    });
})
