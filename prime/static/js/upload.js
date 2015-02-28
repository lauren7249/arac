function selectProfile(url) {
    var params={url:url}
    $.post("/select", params, function(data) {
        if (data.success) {
            window.location = "/confirm"
        }
    });
}

$(function() {
});
