function selectProfile(url) {
    $(".overlay").show();

    var item = choose(['http://54.152.186.2', 'http://54.152.186.2'])

    try {
        $.ajax({
            url: item + ":9090/proxy?url=" + url,
            dataType: 'json',
            success: function(data) {
                var url = data.prospect_url;
                $.post("/select", {url:url}, function(data) {
                    console.log("success");
                    window.location = "/confirm"
                });
            },
            error:function(){
                alert("Error");
            }
        })

    } catch(err) {
        $(".overlay").hide();
        alert("Whoops, something went wrong. Please try again");
    }
}

function choose(choices) {
  var index = Math.floor(Math.random() * choices.length);
  return choices[index];
}

$(function() {
});
