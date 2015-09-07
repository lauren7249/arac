/**
 * Created by Michael Bishop on 8/31/15.
 * Advisor Connect
 */
import './components/helpers.js';
import {AC_Helpers as AC} from './components/helpers.js';
var uuid = require('uuid');

/**
 * @module
 * Background
 */
'use strict';

var runtime = chrome.runtime;
var storage = chrome.storage;
var browserAction = chrome.browserAction;
var qwest = require('qwest');
var ac_uid = undefined;
var ac_is_running = false;

/**
 * Initilization routines
 * @param that Context object
 */
var init = function(that) {

    const kUid_key = 'acUID';
    const kInuse_key = 'acINUSE';

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

    /**
     * Get a value from local storage
     * @param obj Query object or string key
     * @param callback of the type function(obj)
     */
    function getFromStorage(obj = undefined, callback = undefined) {
        console.debug('Getting: ' + obj);
        storage.local.get(obj, callback);
    }

    /**
     * Save a key/value to local storage
     * @param key String key v
     * @param value Object value to save
     * @param cb {function} callback function after save is complete
     */
    function saveToStorage(key = undefined, value = undefined, cb = undefined) {
        var _toSet = {};
        _toSet[key] = value;

        console.debug('saveToStorage ' + key + '/' + value);

        storage.local.set(_toSet, function() {
            if (runtime.lastError !== undefined) {
                console.error('Unable to save value: ' + value + ' for key: ' + key + ' error: ' + runtime.lastError.message);
            } else {
                console.debug('Saved key: ' + key + ' with value: ' + value);
            }
            cb && cb();
        });
    }

    /**
     * UserID getter
     */
    function getUserID() {

        if (that && ac_uid === undefined) {
            // Look for userid in local storage
            getFromStorage(kUid_key, function(obj) {

                if (obj && obj[kUid_key] === undefined) {
                    // No saved id, create a UUID
                    var _uuid = uuid.v4();
                    if (_uuid === undefined) {
                        throw 'UUID was not created, cannot continue without a userid: ' + _uuid;
                    } else {
                        // UUID generated, save to storage, set local variable and return value
                        console.debug('New UID: ' + _uuid.toString());
                        saveToStorage(kUid_key, _uuid, function() {
                            var that = this;
                            that.ac_uid = obj.ac_uid;
                        });

                        return getFromStorage(kUid_key);
                    }
                } else {
                    // Found.  Set local variable and return value
                    console.debug('UID found in storage: ' + obj.ac_uid);
                    ac_uid = obj.ac_uid;
                    return obj.ac_uid;
                }
            });
        }
    }

    runtime.onInstalled.addListener(function(deets) {
        console.debug('On installed reason: ' + deets.reason + ' USER: ' + getUserID());
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

    runtime.onSuspend.addListener(function() {
        ac_is_running = false;
        buttonOff();
        browserAction.setBadgeText({text: ''});
    });

    browserAction.onClicked.addListener(function(tab) {
        //chrome.browserAction.setPopup({popup:'index.html'});
        /**
         * @type obj {Object}
         */
        getFromStorage(kInuse_key, function(obj) {
            console.debug('get ac-in-use');
            obj && console.debug(obj.valueOf());

            if (obj && obj[kInuse_key] === 0 || obj[kInuse_key] === undefined) {

                saveToStorage(kInuse_key, 1);
                buttonOn();

            } else {
                saveToStorage(kInuse_key, 0);
                buttonOff();
            }
        });
    });

    function buttonOn():void {
        browserAction.setIcon({path: 'images/icon_active.png'});
        ac_is_running = true;
    }

    function buttonOff():void {
        browserAction.setIcon({path: 'images/icon.png'});
        ac_is_running = false;
    }

};

init(this);


