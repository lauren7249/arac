var total = 0;
//TODO: stop if logged in
//show captcha if it comes up

function get_url(orig_url) {
	url = orig_url.replace("https://","").replace("http://","");
	console.log(url);
	var fn = url.replace(/\//g, "-") + ".html";
	try {
		var page = get_url_response("https://" + url);
		if (page.toLowerCase().indexOf("captcha") > -1) {
			console.log ("captcha")
			return false
		}
	}
	catch(err) {
		console.log("not loaded")
		return false
	}
	//console.log(page);
	var params = {Key: fn, ContentType:'text/html', Body: page};
	bucket.upload(params, function (err, data) {
		var xmlHttp = new XMLHttpRequest();
		xmlHttp.open( "GET", "http://169.55.28.212:8080/log_uploaded/url=" + orig_url.replace(/\//g, ";").replace(/\?/g, "`"), false );
		xmlHttp.send( null );	
		total += 1;
		countArea.value = total;
		return true
	}); 	
	return true
}

function get_url_response(url) {
	var xmlHttp = new XMLHttpRequest();
	xmlHttp.open( "GET", url, false );
	xmlHttp.send( null );
	var page = xmlHttp.responseText;	
	return page;
}

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

function infinite() {
	var k = 0
	while(true) {
		url = get_url_response("http://169.55.28.212:8080/select")
		if  (url.match(/www./g, url) != null) {
			get_url(url);
		} 
		else {
			break;
		}
		k += 1;
		if (k > 100){
			break;
		} 
	}
	k = 0;

	alert("done!")	
}

document.addEventListener('DOMContentLoaded', function() {
  var checkPageButton = document.getElementById('checkPage');
  countArea = document.getElementById('count');
  checkPageButton.addEventListener('click', function() {
 	var url_field = document.getElementById('query').value;
	if (url_field.length == 0) {
		url_field = get_url_response("http://169.55.28.212:8080/select/n=100")
	}   	

	arr = url_field.match(/[^\r\n]+/g);
	countArea.max = arr.length;
	for (var i in arr) {
		url = arr[i]
		if (false) {
			google(url);
		}
		else {
			success = get_url(url);
			if (!success) { 
				break 
			}
		}
	}

	
  }, false);
}, false);



