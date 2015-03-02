function selectProfile(url) {
    $(".overlay").show();
    var params={url:url}
    try {
        $.post("/select", params, function(data) {
            if (data.success) {
                window.location = "/confirm"
            }
        });
    } catch(err) {
        $(".overlay").hide();
        alert("Whoops, something went wrong. Please try again");
    }
}

$(function() {
});
