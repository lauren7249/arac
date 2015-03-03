function selectProfile(url) {
    $(".overlay").show();

    var item = choose(['http://54.152.186.2', 'http://54.152.181.248'])

    try {
        $.ajax({
            url: item + ":9090/proxy?url=" + url,
            dataType: 'jsonp',
            jsonpCallback: 'redirect',
            error:function(){
                alert("Error");
            }
        })

    } catch(err) {
        $(".overlay").hide();
        alert("Whoops, something went wrong. Please try again");
    }
}

var redirect = function(data) {
    alert(data.prospect_url)
}

function choose(choices) {
  var index = Math.floor(Math.random() * choices.length);
  return choices[index];
}

$(function() {
});
