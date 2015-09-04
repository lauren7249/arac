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

var runtime = chrome.runtime;
var storage = chrome.storage;
var qwest = require('qwest');

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


var init = function(that) {
    runtime.onInstalled.addListener(function(deets) {

        console.debug('On installed reason: ' + deets.reason + ' USER: ' + getUserID(chrome));

    });

    runtime.onStartup.addListener(function() {
        console.log('Startup.');
    });

    runtime.onConnect.addListener(function(port) {
        console.debug(port);
    });

    runtime.onMessage.addListener(function(msg, sender) {
        console.debug(msg);
        console.debug(sender);
    });

    chrome.browserAction.onClicked.addListener(function(tab) {
        chrome.browserAction.setIcon({path: 'images/icon_active.png'});
        //chrome.browserAction.setPopup({popup:'index.html'});
    });
};

var getUserID = function() {

    if (AC.userId === undefined) {
        // Look for userid in local storage
        storage.local.get('ac_userid', function(obj) {

            if (obj.ac_userid === undefined) {
                // No saved id, create a uuid
                var _uuid = uuid.v4();
                if (_uuid === undefined) {
                    throw 'UUID was not created, cannot proceed without a userid : ' + _uuid;
                } else {
                    setUserID(_uuid);
                    return AC.userId;
                }
                // Id was found in local storage.  Set to local variable and return
            } else {
                console.log('Got ' + obj.ac_userid);
                console.log('Returning ' + AC.userId);

                AC.userId = obj.ac_userid;
                return obj.ac_userid;
            }
        });
    }
};

var setUserID = function(id) {
    console.log('SetUserID ' + id);
    AC.userId = id;
    storage.local.set({ac_userid: id}, function() {
        if (runtime.lastError !== undefined) {
            console.error('Unable to save ' + id + 'error: ' + runtime.lastError.message);
        } else {
            console.debug('New userid saved: ' + id);
        }
    });
};

init(this);


