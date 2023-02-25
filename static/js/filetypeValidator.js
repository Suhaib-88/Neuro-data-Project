$(function () {
    $('input[type=file]').change(function () {
        var val = $(this).val().toLowerCase(),
            regex = new RegExp("(.*?)\.(csv|tsv|json|xlsx|zip)$");

        if (!(regex.test(val))) {
            $(this).val('');
            alert('Please select correct file format');
        }
    });
});