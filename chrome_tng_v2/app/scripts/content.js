chrome.tabs.onUpdated.addListener( function (tabId, changeInfo, tab) {
  if (changeInfo.status == 'complete' && tab.active) {
  	if(tab.url.indexOf('linkedin.com/in/') !=-1 || tab.url.indexOf('linkedin.com/pub/') !=-1) {
  		//buttonOn();
		chrome.tabs.executeScript(null, 
			{code: 
				"if (document.documentElement.outerHTML.indexOf('newTrkInfo') != -1) { " +
				    "var linkedin_index = document.documentElement.outerHTML.indexOf('newTrkInfo=') + 12;" +
				    "var linkedin_id = document.documentElement.outerHTML.substring(linkedin_index,linkedin_index+10);" +
				    "var linkedin_id = linkedin_id.substring(0,linkedin_id.indexOf(','));" +
				    "var memberarea = document.getElementsByClassName('public-reg-upsell')[0];" +
				    "var name = document.getElementsByClassName('full-name')[0].innerHTML;" +
				    // "$('<script></script>').appendTo(document.body);" +
				    "var btn = document.createElement('a');" + 
				    "btn.textContent = 'Email ' +name;"+
				    "btn.setAttribute('class', 'signup-button');" + 
				    "btn.setAttribute('target', '_blank');" + 
				    "btn.setAttribute('href', 'http://0.0.0.0:8080/emailLinkedin/lid=' + linkedin_id);" + 
				    "btn.setAttribute('style', 'margin-left: 15px; border-color: #3E85B9 #3E85B9;');" +
				    "btn.style.background='#8CC6E2';" +
				    "memberarea.appendChild(btn);"+
				"}" +
				"else if(document.documentElement.outerHTML.indexOf('memberId') != -1) {" +
					"alert('Please log out of Linkedin or use in incognito to use the extension');"+
				"}"
			}
		);
  	}
  }
})