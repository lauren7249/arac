/**
 * Created by Michael Bishop on 8/31/15.
 * Advisor Connect
 */
import './components/helpers.js';
import {AC} from './components/helpers.js';
var uuid = require('uuid');

/**
 * @module
 * Background
 */
'use strict';

console.log('Loaded.');

var runtime = chrome.runtime;
var storage = chrome.storage;

var init = (that)=> {
    runtime.onInstalled.addListener((deets)=> {

        console.debug('On installed reason: ' + deets.reason);

    });

    runtime.onStartup.addListener(function() {
        console.log('Installed.');
        if (AC.userId === undefined) {
            chrome.storage.local.get({'ac_userid': uuid.v4()}, function(obj) {
                AC.userId = obj;
                console.log('local storage returned:');
                console.log(AC.userId);
            });
        }
    });

    runtime.onConnect.addListener((port)=> {
        console.debug(port);
    });

    runtime.onMessage.addListener((msg, sender)=> {
        console.debug(msg);
        console.debug(sender);
    });

    chrome.browserAction.onClicked.addListener(function(tab) {
        chrome.browserAction.setIcon({path: 'images/icon_active.png'});
        //chrome.browserAction.setPopup({popup:'index.html'});
    });
};

var getUserID = (chrome)=> {

    if (AC.userId === undefined) {
        // Look for userid in local storage
        chrome.storage.local.get('ac_userid', (obj)=> {

            if (obj === undefined) {
                // No saved id, create a uuid
                let uuid = uuid.v4();
                if (uuid === undefined) {
                    throw 'UUID was not created, cannot proceed without a userid : ' + uuid;
                } else {
                    setUserID(chrome, uuid);
                    return uuid;
                }

            } else {
                return obj.ac_userid;
            }
        });
    }
};

var setUserID = (chrome, id) => {
    AC.userId = id;
    chrome.storage.local.set({ac_userid: id}, ()=> {
        if (runtime.lastError !== undefined) {
            console.error('Unable to save ' + id + 'error: ' + runtime.lastError.message);
        }
    });
};

init(this);

/**
 * Default HTTP Options passed
 */
var http_options = {
    cache: false, timeout: 30000, async: true,
    attempts: 1, headers: {
        'Accept-Language': 'en-US'
    }
};

/**
 * Set a limit of 1 HTTP request at a time.  Note
 * this is less than a web browser which can normally
 * make 5 simultaneous requests per domain name
 */
var qwest = require('qwest');
qwest.limit(1);
qwest.setDefaultXdrResponseType('text');
