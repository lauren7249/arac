var HashHack = {
  PREFIX: '#hhMessage=',
  aCallbacks: [],
  sLastHash: '',

  handleInterval: function() {
    var sHash = window.location.hash,
      sDecodedHash, sMessage, i;

    if (sHash !== HashHack.sLastHash) {
      // is it valid
      sDecodedHash = decodeURIComponent(sHash);

      if (0 === sDecodedHash.indexOf(HashHack.PREFIX)) {
        sMessage = sDecodedHash.replace(HashHack.PREFIX, '');
        HashHack.sLastHash = sHash;

        for (i = HashHack.aCallbacks.length - 1; i >=0; i -= 1) {
          HashHack.aCallbacks[i]({data: sMessage});
        }
      }
    }
  },

  init: function() {
    setInterval(HashHack.handleInterval, 250);
  },

  onMessage: function(fnCallback) {
    HashHack.aCallbacks.push(fnCallback);
  }
};
HashHack.init();