var fs      = require('fs'),
    webpage = require('webpage'),
    system  = require('system');

var url     = system.args[1],
    outpath = system.args[2];

var page = webpage.create();
page.open(url, function() {
    fs.write(outpath, page.content);
    phantom.exit();
});
