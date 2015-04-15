$(function() {
    bindButtons();
});

function bindButtons() {
    $("#show-user-profile").click(function() {
        $(".user-profile-tabs li").removeClass("active");
        $(this).parent().addClass("active");
        $(".prospect-profile-results").hide();
        $(".profile-content").fadeIn();

    });

    $("#show-user-prospects").click(function() {
        $(".user-profile-tabs li").removeClass("active");
        $(this).parent().addClass("active");
        $(".profile-content").hide();
        $(".prospect-profile-results").fadeIn();
    });

    $(".add-user-prospect").click(function(event) {
        if (!event.fired) {
            $(this).html("Added!");
            event.fired = true;
            var id = $(this).data("id");
            $.post("/user/prospect/add/" + id, function(data) {
                bootbox.alert("Prospect added to prospect list!");
            });
            return false;
        }
    });

    $(".remove-user-prospect").click(function(event) {
        if (!event.fired) {
            event.fired = true;
            var id = $(this).data("id");
            $.post("/user/prospect/skip/" + id, function(data) {
                bootbox.alert("Prospect skipped.");
            });
            return false;
        }
    });
}
