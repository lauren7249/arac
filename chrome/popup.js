var xmlHttp
var total = 0;
var countArea;

//TODO: stop if logged in
//TODO: show captcha if it comes up


/**
 * Retrieve the content of a url
 * @param orig_url
 * @returns {boolean}
 *
 * TODO Assumes all urls have an https:// is this as safe assumption?
 * FIXME Gracefully handle captcha
 */
function get_url(orig_url) {
    var url = orig_url.replace("https://", "").replace("http://", "");
    console.log(url);
    var fn = url.replace(/\//g, "-") + ".html";
    get_url_response("https://" + url, function () {

    });
    try {
        var page = get_url_response("https://" + url);
        if (page.toLowerCase().indexOf("captcha") > -1) {
            console.log("captcha");
            return false
        }
    }
    catch (err) {
        console.log("not loaded");
        return false
    }
    //console.log(page);
    var params = {Key: fn, ContentType: 'text/html', Body: page};
    bucket.upload(params, function (err, data) {
        var xmlHttp = new XMLHttpRequest();
        xmlHttp.open("GET", "http://169.55.28.212:8080/log_uploaded/url=" + orig_url.replace(/\//g, ";").replace(/\?/g, "`"), false);
        xmlHttp.send(null);
        total += 1;
        countArea.value = total;
        return true
    });
    return true
}

/**
 * Make an asynchronous HTTP call and execute the
 * callback on success
 *
 * @param url
 * @param callback function on success
 *
 * TODO Error callback
 */
//function get_url_response(url, callback) {
//    xmlHttp = new XMLHttpRequest();
//    xmlHttp.onreadystatechange = callback;
//    xmlHttp.open("GET", url, true);
//    xmlHttp.setRequestHeader('Cache-Control', 'no-cache');
//    xmlHttp.setRequestHeader('Accept-Language', 'en-US');
//    xmlHttp.send(null);
//}

//function is_google(url) {
//    return url.match(/www.google.com/g, url) != null;
//}
//
//function google(url) {
//    console.log("is google");
//}

/**
 * Initialize the Amazon Cognito credentials provider
 */
//function initAWS() {
//    AWS.config.region = 'us-east-1'; // Region
//    AWS.config.credentials = new AWS.CognitoIdentityCredentials({
//        IdentityPoolId: 'us-east-1:d963e11a-7c9b-4b98-8dfc-8b2a9d275574',
//    });
//    var bucket = new AWS.S3({params: {Bucket: 'chrome-ext-uploads'}});
//}

/**
 * Callback function that checks that xmlHttpRequest has completed
 * and runs a callback on success.
 *
 * @param callback Function to run on success
 */
function onHttpComplete(callback) {
    console.debug(xmlHttp.status);
    if (xmlHttp.readyState == XMLHttpRequest.DONE && xmlHttp.status == 200) {
        callback();
    } else if (xmlHttp.readyState = XMLHttpRequest.DONE && xmlHttp.status != 200) {
        console.error(xmlHttp.statusText)
        console.error(xmlHttp.responseText)
    }
}

/**
 * Selects all outstanding urls and processes up to 100 (I think)
 * Function not called -- maybe used for testing else eligible for
 * deletion.
 *
 * TODO Is this used?
 */
function infinite() {

    var k = 0, url = null;

    while (true) {
        get_url_response("http://169.55.28.212:8080/select", function () {
            onHttpComplete(function () {
                url = xmlHttp.responseText;
                if (url.match(/www./g, url) != null) {
                    get_url(url);
                }
                else {
                    break;
                }
            });
        });
        k += 1;
        if (k > 100) {
            break;
        }
    }

    alert("done!")
}

/**
 * Initialization function executed after DOM is loaded
 */
document.addEventListener('DOMContentLoaded', function () {
    initAWS();
    var checkPageButton = document.getElementById('checkPage');
    var countArea = document.getElementById('count');
    checkPageButton.addEventListener('click', function () {
        var url_field = document.getElementById('query').value;
        if (url_field.length == 0) {
            get_url_response("http://169.55.28.212:8080/select/n=100", function () {
                onHttpComplete(function () {
                    var url, success;

                    url_field = xmlHttp.responseText;
                    var arr = url_field.match(/[^\r\n]+/g);

                    countArea.max = arr.length;
                    for (var i in arr) {
                        url = arr[i];
                        success = get_url(url);
                        if (!success) {
                            break
                        }
                    }
                });
            });
        }

    }, false);
}, false);



