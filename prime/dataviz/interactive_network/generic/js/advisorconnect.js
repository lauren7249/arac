$( document ).ready(function() {
    var quotes = $(".quotes");
    var quoteIndex = -1;
    
    function showNextQuote() {
        ++quoteIndex;
        quotes.eq(quoteIndex % quotes.length)
            .fadeIn(3000)
            .delay(3000)
            .fadeOut(3000, showNextQuote);
    }
    
    showNextQuote();

    $('.fancybox-media').fancybox({
        openEffect  : 'elastic',
        closeEffect : 'none',
        helpers : {
            media : {}
        }
    });

});