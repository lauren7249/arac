var HashHack = {
  PREFIX: '#hhMessage=',

  postMessage: function(el, sMessage) {
    if ('string' === typeof el) {
      el = document.getElementById(el);
    }

    var sUrl = el.src.replace(/#.*/, '');
    el.src = sUrl + HashHack.PREFIX + encodeURIComponent(sMessage);
  }
};