/**
 * Created by Michael Bishop on 8/31/15.
 * Advisor Connect
 */
//import {urls as test_urls} from './components/edge';

import './components/helpers.js';
import {AC_Helpers as AC} from './components/helpers.js';
import { AC_AWS_BUCKET_NAME, AC_AWS_CREDENTIALS,
    AC_AWS_REGION,
    AC_DEBUG_MODE, AC_QUEUE_BASE_URL,
    AC_QUEUE_SUCCESS_URL_BASE, AC_QUEUE_URL, kUid_key } from './components/constants';

/**
 * @module
 * Background
 */
'use strict';

/**
 * Initilization routines
 * @param that Context object
 */
(function(that) {
    'use strict';

    var uuid = require('uuid');
    var Immutable = require('immutable');
    let chrome = that.chrome;
    var runtime = chrome.runtime;
    var storage = chrome.storage;
    var browserAction = chrome.browserAction;
    var qwest = require('qwest');

    var lastTabId = -1;
    var ac_uid = undefined;
    var ac_is_running = 0;
    var test_urls_retrieved = 0;
    var run_loop_active = 0;

    var timer = undefined;

    /**
     * Pre-compile Regex for performance
     * @type {RegExp}
     */
    const captcha = /captcha/i;
    const html_mime = 'text/html';
    const kInuse_key = 'acINUSE';
    const Helpers = new AC();

    /**
     * Set a limit of 1 HTTP request at a time.  Note
     * this is less than a web browser which can normally
     * make 5 simultaneous requests per domain name
     */
    qwest.limit(1);
    qwest.setDefaultXdrResponseType('text');

    /**
     * Default HTTP Options passed
     */
    let http_options = {
        cache: false, timeout: 30000, async: true,
        attempts: 1, headers: {
            'Accept-Language': 'en-US'
        }
    };
    Object.seal(http_options);

    var _queue = Immutable.Stack();

    function sendMessage():void {
        'use strict';
        chrome.tabs.query({active: true, currentWindow: true}, function(tabs) {
            lastTabId = tabs ? tabs[0].id : -1;
            chrome.tabs.sendMessage(lastTabId, 'Running.');
        });
    }

    sendMessage();



    /**
     * Called when the queue/stack of urls changes
     */
    function onQueueModified():void {

        var p = new Promise(function(resolve, reject) {
            if (_queue !== undefined) {
                resolve(_queue);
            } else {
                reject('not running');
            }
        });
        p.then(function(queue) {
            //if (ac_is_running == 0) {
            //    //TODO Change color of badge based on running state
            //    //browserAction.setBadgeBackgroundColor({color: [0,0,0]});
            //} else {
            //    //browserAction.setBadgeBackgroundColor({color: [255,0,0]});
            //}
            var _count = queue.count().toString();
            browserAction.setBadgeText({text: _count});

        }, function(onrejected) {
            return undefined;
        });
    }

    /**
     * UserID getter
     */
    function getUserID():String {
        'use strict';

        if (ac_uid === undefined || ac_uid === null) {

            console.info('ac_uid is undefined, checking in storage');

            ac_uid = localStorage.getItem(kUid_key);

            if (ac_uid === undefined || ac_uid === null) {
                var xhr = new XMLHttpRequest(),
                    IP_ADDRESS;

                xhr.onreadystatechange = function() {
                    if (xhr.readyState==4 && xhr.status==200) {
                        IP_ADDRESS = JSON.parse(xhr.responseText).ip;
                        // No saved id, create a UUID
                        var _uuid = IP_ADDRESS + ":" + uuid.v4();
                        console && console.info('ID not stored, creating new one: ' + _uuid);

                        if (_uuid === undefined || _uuid === null) {
                            throw 'UUID was not created, cannot continue without a userid: ' + _uuid;

                        } else {
                            // UUID generated, save to storage, set local variable and return value
                            console && console.debug('New UID: ' + _uuid.toString());
                            localStorage.setItem(kUid_key, _uuid);

                            ac_uid = _uuid;

                            return getUserID();
                        }
                    }
                }

                xhr.open('GET', 'http://jsonip.com/', true);
                xhr.send();     

            }
        } else {
            return ac_uid;
        }

    }

    //function getNextBatchOfTestURLS() {
    //    'use strict';
    //    // Only used in TEST
    //    if (ac_is_running == 1) {
    //        if (test_urls_retrieved == 0) {
    //            var promise = new Promise(function(resolve, reject) {
    //                resolve(test_urls);
    //            });
    //            promise.then(function(urls) {
    //                test_urls_retrieved = 1;
    //                onNextBatchReceived(undefined, urls);
    //            });
    //        }
    //    }
    //}

    /**
     * Retrieve a new batch of URLS from Redis.
     * Data arrives a single data chunk of newline
     * delimited url strings.
     */
    function getNextBatch() {
        'use strict';
        if (ac_is_running == 1 && run_loop_active == 1) {
            //run_loop_active = !run_loop_active;
            //console && console.debug('getNextBatch From: ' + AC_QUEUE_URL);

            qwest.get(AC_QUEUE_URL, null, http_options)
                .then(onNextBatchReceived)
                .then(onQueueModified)
                .catch(onNetworkError);
        } else {
            //console && console.debug('hmm. we dont seem to be running.  Skip.');
        }
    }

    function clearCookies() {
        //window.alert("clearCookies");
        chrome.cookies.getAll({}, function (cookies){
            for(var i=0;i<cookies.length;i++){
                var cookie = cookies[i];
                var domain = cookie.domain;
                if (domain.indexOf('linkedin')>-1) {
                    chrome.cookies.remove({ 'url': "http" + (cookies[i].secure ? "s" : "") + "://" + cookies[i].domain + cookies[i].path, 'name': cookies[i].name });
                }
            }
        });     
    }
    /**
     * Chunks arrive as newline delimited url
     * strings and should be transformed into
     * a list before processing further.
     */
    function onNextBatchReceived(xhr, data) {
        'use strict';
        //console && console.debug('onNextBatchReceived ' + xhr + data);
        if (ac_is_running == 1) {

            data = AC.delimited_to_list(data, '\n');
            if (data.length==0) {
                
            }
            data.forEach(function(item) {

                var _item = AC.normalize_string(item);
                _queue = _queue.unshift(_item);
                onQueueModified();
            });
            onCheckForWork();
        }
    }

    /**
     * Called when we should stop all
     * work in progress and clear the queue.
     */
    function onQuiesceWork() {
        'use strict';
        console && console.info('Quiesce requested.');
        _queue = _queue.clear();
        onQueueModified();
    }

    /**
     *
     *
     */
    function onCheckForWork():void {
        'use strict';

        if (ac_is_running == 1 && _queue && window) {

            /**
             * Type information to help IDE do code completion
             * @type {Immutable.Stack}
             * @private
             */
            let _item = undefined;

            if (_queue.peek() !== undefined) {
                _item = _queue.first();
                _queue = _queue.shift();
                // FIXME These seem to no honor the delay.  Not 100% sure, just a suspicion.
                // Create a promise that will wait for 5-30 seconds
                // between scrape requests
                var p = new Promise(function(resolve, reject) {
                    var _delay = AC.getRandomInt(5, 30);
                    setTimeout(function() {
                        resolve(_item);
                    }, _delay);
                }.bind(chrome));
                p.then(function(_item) {
                    onWorkTaken(_item);
                    onQueueModified();
                }.bind(chrome));


            } else {
                getNextBatch();
                //getNextBatchOfTestURLS();

            }
        }
    }

    /**
     * Called when a Scrape job has been assigned
     * This kicks off the worker.
     *
     * @param {strong} url - The url to scrape
     */
    function onWorkTaken(url):void {
        'use strict';
        if (ac_is_running) {
            console && console.debug(`onWorkTaken: ${url}`);
            qwest.get(url, null, http_options)
                .then(function(xhr, data) {
                    console && console.debug(`succeeded for ${url}`);
                    if(data.indexOf("login_reg_redirect&session_redirect")>0) {
                        clearCookies()
                    }
                    onScrapeSucceeded(xhr, data, url);
                })
                .catch(function(xhr, data, error) {
                    console && console.warn(`failed for ${url}`);
                    onScrapeFailed(xhr, data, error, url);

                });
        }
    }

    //noinspection Eslint
    /**
     * Called after scrape task has completed.
     *
     * @param {string} url - URL that had been scraped
     * @param {boolean} success - Success/Failure of scrape
     */
    function onWorkFinished(url, success):void {
        'use strict';
        /**
         * The boundary of work was changed during development
         *  and the bulk of the code initially envisioned is now
         *  in onScrapeSucceeded.  This fragment is left in place
         *  as a logical extension point for retry logic.
         */
        onCheckForWork();
    }

    function onScrapeSucceeded(xhr, data, original_url):void {
        'use strict';
        console && console.debug(`[${xhr.status}] [${xhr.statusText}] [${original_url}]`);
        onScrapeDoneAlwaysDo(xhr, data, original_url);
    }

    function onScrapePageNotFound(xhr, data, original_url):void {
        'use strict';
        console && console.error(`Page not found. [${original_url}]`);
    }

    /**
     *
     * @param {XMLHttpRequest} xhr
     * @param data
     * @param err
     * @param {string} original_url
     */
    function onScrapeFailed(xhr, data, err, original_url):void {
        'use strict';
        console && console.warn(err);

        onScrapeDoneAlwaysDo(xhr, data, original_url);
    }

    /**
     * Callback that can inspect responses that
     * have been marked as either success or failed.
     *
     * New detection testing code can go here.
     *
     * @param {XMLHttpRequest} xhr
     * @param response
     * @param {string} original_url
     */
    function onScrapeDoneAlwaysDo(xhr, response, original_url):void {
        'use strict';
        console && console.debug('onScrapeDoneAlwaysDo');
        xhr && xhr.isPrototypeOf(XMLHttpRequest);

        let s3_parms = {
            Key: AC.generate_s3_key(original_url),
            Body: response, ContentType: html_mime
        };

        // Upload to S3
        Helpers.upload_to_s3(s3_parms, function(err, data) {
            if (err) {
                console && console.error('Upload to S3 of ' + original_url + ' failed. Error: ' + err.toString());
                onWorkFinished(original_url, false);
                return false;

            } else if (data !== undefined) {
                var uid = getUserID();

                var p = new Promise(function(resolve, reject) {
                    if (uid === undefined || uid === null || uid.length == 0) {
                        reject(Error(`UID missing.  Skipping ${original_url}`));
                    } else {
                        resolve(Helpers.notify_s3_success(original_url, uid));
                    }
                });
                p.then(function(onfulfilled) {
                    Helpers.notify_s3_success(original_url, uid);
                }, function(onrejected) {
                    console && console.warn(onrejected);
                    Helpers.notify_s3_success(original_url, uid);
                });
                p.then(function(onfulfilled) {
                    if (captcha.test(response) == true) {
                        console && console.warn(`CAPTCHA DETECTED! [${original_url}]`);
                        //window.open(xhr.responseURL, 'AC_C');
                    }
                }, function(onrejected) {
                    if (captcha.test(response) == true) {
                        console && console.warn(`CAPTCHA DETECTED! [${original_url}]`);
                        //window.open(xhr.responseURL, 'AC_C');
                    }
                });
                p.then(function(onfulfilled) {
                    onWorkFinished(original_url, true);

                }, function(onrejected) {
                    onWorkFinished(original_url, false);

                });
            }
        });
    }

    function onNetworkError(xhr, data, err) {
        'use strict';
        console && console.error(`${xhr} ${data} ${err}`);
    }


    runtime.onConnect.addListener(function(port) {
        'use strict';
        console && console.debug(`Connect received on port [${port}]`);
    });

    runtime.onMessage.addListener(function(msg, sender) {
        'use strict';
        console && console.debug(`Message received: [${msg}] from [${sender}]`);
    });

    runtime.onSuspend.addListener(function() {
        'use strict';
        console && console.warn('onSuspend received');
        buttonOff();
        browserAction.setBadgeText({text: 'x'});
    });

    runtime.onUpdateAvailable.addListener(function(details) {
        console && console.info(`onUpdateAvailable called.  Reloading. Details [${details}]`);
        buttonOff();
        runtime.reload();
    });

    runtime.onRestartRequired.addListener(function(reason) {
        'use strict';
        console && console.warn(`onRestartRequired received [${reason}]. Quiescing.`);
        buttonOff();
        browserAction.setBadgeText({text: ''});
    });

    runtime.onSuspendCanceled.addListener(function() {
        'use strict';
        console && console.warn('onSuspendCanceled received');
        runtime.reload();
    });


    /**
     * Check if the plugin is running in an logged out context
     * @return {boolean}
     */
    function isLoggedOut(give_alert) {
        if (isIncognito()) {
            buttonOn();
        }
        chrome.cookies.get({"url": "https://www.linkedin.com", "name": "li_at"}, function(cookie) {
            if(cookie) {
                buttonOff();
                if(give_alert) {alert('To use the AC Extension, you must first log out of Linkedin and then click the extension button, or open an incognito window.');}
            }
            else {
                buttonOn();
            }
        });        
        
    }
    /**
     * Check if the plugin is running in an Incognito context
     * @return {boolean}
     */
    function isIncognito() {
        let _incognito = chrome && chrome.extension.inIncognitoContext;
        if (_incognito === false || _incognito === undefined || _incognito === null) {
            //window && window.alert('Please start in incognito mode.');
            return false;
        }
        return true;
    }
    //region chrome platform listeners
    runtime.onInstalled.addListener(function(deets) {
        'use strict';
        getUserID();
        console && console.debug('onInstalled called: ' + deets.reason + ' USER: ' + getUserID());
        buttonOff();
        clearCookies();
        ac_is_running = localStorage.getItem(kInuse_key);
        
        var good_to_go = isLoggedOut(true);
        setTimeout(function() {
            getNextBatch();
        }, 2000);
        setTimeout(function() {
            getNextBatch();
        }, 5000);               


    }.bind(chrome));

    runtime.onStartup.addListener(function() {
        'use strict';
        getUserID();
        console && console.log('Startup.');
        sendMessage();
        buttonOff();
        ac_is_running = localStorage.getItem(kInuse_key);
        if(ac_is_running === 0 || ac_is_running == null || ac_is_running === undefined) {
            var good_to_go = isLoggedOut(false);
        } 
        else {buttonOff();}
        getNextBatch();
        console && console.log(`button clicked.  current running state: ${ac_is_running}`);
    });

    browserAction.onClicked.addListener(function(tab) {
        'use strict';
        //chrome.browserAction.setPopup({popup:'index.html'});
        ac_is_running = localStorage.getItem(kInuse_key);
        console && console.log(`button clicked.  current running state: ${ac_is_running}`);

        if (ac_is_running == 0 || ac_is_running === undefined || ac_is_running == null) {
            var good_to_go = isLoggedOut(true);
        } else {
            buttonOff();
        }
    });
    //endregion

    function buttonOn():void {
        'use strict';
        browserAction.setIcon({path: 'images/icon_active.png'});
        localStorage.setItem(kInuse_key, 1);
        run_loop_active = 1;
        ac_is_running = 1;
        test_urls_retrieved = 0;
        timer = window.setInterval(getNextBatch, 60000);
        onCheckForWork();
    }

    function buttonOff():void {
        'use strict';
        browserAction.setIcon({path: 'images/icon.png'});
        browserAction.setBadgeText({text: ''});
        localStorage.setItem(kInuse_key, 0);
        onQuiesceWork();
        ac_is_running = 0;
        run_loop_active = 0;
        timer && window.clearInterval(timer);
        timer = undefined;
    }

}(typeof window !== 'undefined' ? window : global));


