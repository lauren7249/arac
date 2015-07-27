var total = 0;

function get_url(orig_url) {
	url = orig_url.replace("https://","").replace("http://","");
	console.log(url);
	var fn = url.replace(/\//g, "-") + ".html";
	var page = get_url_response("https://" + url);
	//console.log(page);
	var params = {Key: fn, ContentType:'text/html', Body: page};
	bucket.upload(params, function (err, data) {
		var xmlHttp = new XMLHttpRequest();
		xmlHttp.open( "GET", "http://169.55.28.212:8080/log_uploaded/url=" + orig_url.replace(/\//g, ";"), false );
		xmlHttp.send( null );	
		total += 1;
		countArea.value = total;
	}); 	
}

function get_url_response(url) {
	var xmlHttp = new XMLHttpRequest();
	xmlHttp.open( "GET", url, false );
	xmlHttp.send( null );
	var page = xmlHttp.responseText;	
	return page;
}
//var XMLHttpRequest = require("xmlhttprequest").XMLHttpRequest;
//var page = get_url_response("http://www.google.com/search?q=site%3Awww.linkedin.com+Lauren+Talbot+advisorCONNECT&es_sm=91&ei=NZxTVY_lB8mPyATvpoGACg&sa=N&num=100&start=0");
function is_google(url) {
	return url.match(/www.google.com/g, url) != null;
}

function google(url) {
	console.log("is google");
}

// Initialize the Amazon Cognito credentials provider
AWS.config.region = 'us-east-1'; // Region
AWS.config.credentials = new AWS.CognitoIdentityCredentials({
    IdentityPoolId: 'us-east-1:d963e11a-7c9b-4b98-8dfc-8b2a9d275574',
});
var bucket = new AWS.S3({params: {Bucket: 'chrome-ext-uploads'}});

document.addEventListener('DOMContentLoaded', function() {
  var checkPageButton = document.getElementById('checkPage');
  countArea = document.getElementById('count');
  checkPageButton.addEventListener('click', function() {
 	var url_field = document.getElementById('query').value;
	if (url_field.length == 0) {
		var xmlHttp = new XMLHttpRequest();
		xmlHttp.open( "GET", "http://169.55.28.212:8080/select", false );
		xmlHttp.send( null );
		url = xmlHttp.responseText;
		get_url(url);
	} 
	else {
		arr = url_field.match(/[^\r\n]+/g);
		console.log(arr.length);
		countArea.max = arr.length;
		for (var i in arr) {
			url = arr[i]
			if (is_google(url)) {
				google(url);
			}
			else {
				get_url(url);
			}
		}	
	}
  }, false);
}, false);