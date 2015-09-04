/**
 * Created by Michael Bishop on 8/31/15.
 * Advisor Connect
 */
import './components/helpers.js';
import {AC as AC} from './components/helpers.js';
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

let isRuning = false;
var ac_uid = undefined;
/**
 * Initilization routines
 * @param that Context object
 */
var init = function(that) {
    runtime.onInstalled.addListener(function(deets) {

        console.debug('On installed reason: ' + deets.reason + ' USER: ' + getUserID(that));

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


/**
 * UserID getter
 * @param that Context Object
 */
function getUserID(that) {

    if (that.ac_uid === undefined) {
        // Look for userid in local storage
        getFromStorage(that, 'ac_uid', function(obj) {

            if (obj.ac_uid === undefined) {
                // No saved id, create a UUID
                var _uuid = uuid.v4();
                if (_uuid === undefined) {
                    throw 'UUID was not created, cannot continue without a userid: ' + _uuid;
                } else {
                    // UUID generated, save to storage, set local variable and return value
                    saveToStorage(that, 'ac_uid', _uuid);
                    that.ac_uid = obj.ac_uid;
                    return obj.ac_uid;
                }
            } else {
                // Found.  Set local variable and return value
                that.ac_uid = obj.ac_uid;
                return obj.ac_uid;
            }
        });
    }
}


/**
 * Get a value from local storage
 * @param that Context
 * @param obj Query object or string key
 * @param callback of the type function(obj)
 */
function getFromStorage(that = this, obj = {}, callback = undefined) {
    storage.local.get(obj, callback);
}

/**
 * Save a key/value to local storage
 * @param that Context object
 * @param key String key value
 * @param value Object value to save
 */
function saveToStorage(that = this, key = undefined, value = undefined) {
    console.debug('saveToStorage ' + key + '/' + value);
    storage.local.set({key: value}, function() {
        if (runtime.lastError !== undefined) {
            console.error('Unable to save value: ' + value + ' for key: ' + key + ' error: ' + runtime.lastError.message);
        } else {
            console.debug('Saved key: ' + key + ' for value: ' + value);
        }
    });
}

init(this);


