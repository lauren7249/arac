/**
 * Created by Michael Bishop on 8/31/15.
 * Advisor Connect
 */
import {urls as test_urls} from './components/edge';

import './components/helpers.js';
import {AC_Helpers as AC} from './components/helpers.js';
import { AC_AWS_BUCKET_NAME, AC_AWS_CREDENTIALS,
    AC_AWS_REGION,
    AC_DEBUG_MODE, AC_QUEUE_BASE_URL,
    AC_QUEUE_SUCCESS_URL_BASE, AC_QUEUE_URL } from './components/constants';

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

    var Observable = require('observe-js');
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

    /**
     * Pre-compile Regex for performance
     * @type {RegExp}
     */
    const captcha = /captcha/i;
    const html_mime = 'text/html';
    const kUid_key = 'acUID';
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
    var queue = Immutable.Stack();

    function sendMessage():void {
        'use strict';
        chrome.tabs.query({active: true, currentWindow: true}, function(tabs) {
            lastTabId = tabs[0].id;
            chrome.tabs.sendMessage(lastTabId, "Background page started.");
        });
    }

    sendMessage();

    function onQueueModified():Promise {

        return new Promise(function(resolve, reject) {
            if (ac_is_running) {
                let _count = queue.size.toString();
                browserAction.setBadgeText({text: _count});
                resolve();
            } else {
                reject();
            }
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

                // No saved id, create a UUID
                var _uuid = uuid.v4();
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
        } else {
            return ac_uid;
        }

    }

    function getNextBatchOfTestURLS() {
        'use strict';
        // Only used in TEST
        if (ac_is_running == 1) {
            if (test_urls_retrieved == 0) {
                var promise = new Promise(function(resolve, reject) {
                    resolve(test_urls);
                });
                promise.then(function(urls) {
                    test_urls_retrieved = 1;
                    onNextBatchReceived(undefined, urls);
                });
            }
        }
    }

    /**
     * Retrieve a new batch of URLS from Redis.
     * Data arrives a single data chunk of newline
     * delimited url strings.
     */
    function getNextBatch() {
        'use strict';
        if (ac_is_running == 1) {
            console.debug('getNextBatch From: ' + AC_QUEUE_URL);
            qwest.get(AC_QUEUE_URL, null, http_options)
                .then(onNextBatchReceived)
                .catch(onNetworkError);
        }
    }

    /**
     * Chunks arrive as newline delimited url
     * strings and should be transformed into
     * a list before processing further.
     */
    function onNextBatchReceived(xhr, data) {
        'use strict';
        console && console.debug('onNextBatchReceived ' + xhr + data);
        if (ac_is_running == 1) {

            data = AC.delimited_to_list(data, '\n');
            data.forEach(function(item) {

                var _item = AC.normalize_string(item);
                queue = queue.unshift(_item);
                onCheckForWork();
            });
        }
    }

    /**
     * Called when we should stop all
     * work in progress and clear the queue.
     */
    function onQuiesceWork() {
        'use strict';
        console && console.info('Quiesce requested.');
        queue = queue.clear();
    }

    /**
     *
     *
     */
    function onCheckForWork() {
        'use strict';

        if (ac_is_running == 1) {

            /**
             * Type information to help IDE do code completion
             * @type {Immutable.Stack}
             * @private
             */
            let _queue = queue;
            let _item = undefined;

            if (_queue.peek() !== undefined) {
                _item = _queue.first();
                queue = _queue.shift();
                // Create a promise that will wait for 5-30 seconds
                // between scrape requests
                var p = new Promise(function(resolve, reject) {
                    var _delay = AC.getRandomInt(5, 30);
                    window.setTimeout(
                        function() {
                            console.log(_delay);
                            resolve();
                        },
                        _delay);
                });
                p.then(function() {
                    console && console.debug('calling onWorkTaken');
                    onWorkTaken(_item);
                });


            } else {
                getNextBatchOfTestURLS();
                //getNextBatch();
            }
        }
    }

    /**
     * Called when a Scrape job has been assigned
     * This kicks off the worker.
     *
     * @param {strong} url - The url to scrape
     */
    function onWorkTaken(url) {
        'use strict';
        qwest.get(url, null, http_options)

            .then(function(xhr, data) {
                onScrapeSucceeded(xhr, data, url);
            })
            .catch(function(xhr, data, error) {
                onScrapeFailed(xhr, data, error, url);
            });
    }

    //noinspection Eslint
    /**
     * Called after scrape task has completed.
     *
     * @param {string} url - URL that had been scraped
     * @param {boolean} success - Success/Failure of scrape
     */
    function onWorkFinished(url, success) {
        'use strict';
        /**
         * The boundary of work was changed during development
         *  and the bulk of the code initially envisioned is now
         *  in onScrapeSucceeded.  This fragment is left in place
         *  as a logical extension point for retry logic.
         */
        onCheckForWork();
    }

    function onScrapeSucceeded(xhr, data, original_url) {
        'use strict';
        console && console.debug(`[${xhr.status}] [${xhr.statusText}] [${original_url}]`);
        onScrapeDoneAlwaysDo(xhr, data, original_url);
    }

    function onScrapePageNotFound(xhr, data, original_url) {
        'use strict';
        console && console.error(`Page not found. [${original_url}]`);
    }

    /**
     *
     * @param  {XMLHttpRequest} xhr
     * @param data
     * @param err
     * @param {string} original_url
     */
    function onScrapeFailed(xhr, data, err, original_url) {
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
    function onScrapeDoneAlwaysDo(xhr, response, original_url) {
        'use strict';
        xhr && xhr.isPrototypeOf(XMLHttpRequest);

        let s3_parms = {
            Key: AC.generate_s3_key(original_url),
            Body: response, ContentType: html_mime
        };

        // Upload to S3
        Helpers.upload_to_s3(s3_parms, function(err, data) {
            if (err) {
                console && console.error('Upload to S3 of ' + original_url + ' failed. Error: ' + err.toString());
                return onWorkFinished(original_url, false);

            } else if (data !== undefined) {
                var uid = getUserID();
                if (uid === undefined || uid === null) {
                    throw 'UID missing.  Aborting';
                }


                Helpers.notify_s3_success(original_url, uid);

                if (captcha.test(response) == true) {
                    console && console.warn(`CAPTCHA DETECTED! [${original_url}]`);
                    //window.open(xhr.responseURL, 'AC_C');
                }
            }

            onWorkFinished(original_url, true);
        });
    }

    function onNetworkError(xhr, data, err) {
        'use strict';
        console && console.error(`${xhr} ${data} ${err}`);
    }

    //region chrome platform listeners
    runtime.onInstalled.addListener(function(deets) {
        'use strict';
        getUserID();
        console && console.debug('onInstalled called: ' + deets.reason + ' USER: ' + getUserID());
        buttonOff();
        onQuiesceWork();
    });

    runtime.onStartup.addListener(function() {
        'use strict';
        getUserID();
        console && console.log('Startup.');
    });

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
        onQuiesceWork();
        buttonOff();
        browserAction.setBadgeText({text: 'Q'});
    });

    runtime.onUpdateAvailable.addListener(function(details) {
        console && console.info(`onUpdateAvailable called.  Reloading. Details [${details}]`);
        onQuiesceWork();
        buttonOff();
        runtime.reload();
    });

    runtime.onRestartRequired.addListener(function(reason) {
        'use strict';
        console && console.warn(`onRestartRequired received [${reason}]. Quiescing.`);
        onQuiesceWork();
        buttonOff();
        browserAction.setBadgeText({text: ''});
    });

    runtime.onSuspendCanceled.addListener(function() {
        'use strict';
        console && console.warn('onSuspendCanceled received');
    });

    browserAction.onClicked.addListener(function(tab) {
        'use strict';
        //chrome.browserAction.setPopup({popup:'index.html'});

        ac_is_running = localStorage.getItem(kInuse_key);
        console && console.debug(`button clicked.  current running state: ${ac_is_running}`);

        if (ac_is_running == 0 || ac_is_running === undefined) {

            buttonOn();
            onCheckForWork();
        } else {

            buttonOff();
            onQuiesceWork();
        }
    });
    //endregion

    function buttonOn():void {
        'use strict';
        browserAction.setIcon({path: 'images/icon_active.png'});
        localStorage.setItem(kInuse_key, 1);
        ac_is_running = 1;
        test_urls_retrieved = 0;
    }

    function buttonOff():void {
        'use strict';
        browserAction.setIcon({path: 'images/icon.png'});
        localStorage.setItem(kInuse_key, 0);
        ac_is_running = 0;
    }

}(typeof window !== 'undefined' ? window : global));



