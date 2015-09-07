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


/**
 * Initilization routines
 * @param that Context object
 */
var init = function(that) {

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

    browserAction.onClicked.addListener(function(tab) {
        //chrome.browserAction.setPopup({popup:'index.html'});
        getFromStorage('ac_in_use', function(obj) {
            console.debug('get ac-in-use');
            console.debug(obj.toString());

            if (obj && obj['ac_in_use'] === 0 || obj['ac_in_use'] === undefined) {

                console.log('button going on');
                saveToStorage('ac_in_use', 1);
                buttonOn();

            } else {
                console.log('button going off');
                saveToStorage('ac_in_use', 0);
                buttonOff();
            }
        });
    });

    function buttonOn():void {
        browserAction.setIcon({path: 'images/icon_active.png'});
    }

    function buttonOff():void {
        browserAction.setIcon({path: 'images/icon.png'});
    }


    /**
     * UserID getter
     * @param that Context Object
     */
    function getUserID() {

        if (that && ac_uid === undefined) {
            // Look for userid in local storage
            getFromStorage('ac_uid', function(obj) {

                if (obj && obj['ac_uid'] === undefined) {
                    // No saved id, create a UUID
                    var _uuid = uuid.v4();
                    if (_uuid === undefined) {
                        throw 'UUID was not created, cannot continue without a userid: ' + _uuid;
                    } else {
                        // UUID generated, save to storage, set local variable and return value
                        saveToStorage('ac_uid', _uuid);
                        ac_uid = obj.ac_uid;
                        return obj.ac_uid;
                    }
                } else {
                    // Found.  Set local variable and return value
                    ac_uid = obj.ac_uid;
                    return obj.ac_uid;
                }
            });
        }
    }

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
     */
    function saveToStorage(key = undefined, value = undefined) {
        console.debug('saveToStorage ' + key + '/' + value);
        storage.local.set({key: value}, function() {
            if (runtime.lastError !== undefined) {
                console.error('Unable to save value: ' + value + ' for key: ' + key + ' error: ' + runtime.lastError.message);
            } else {
                console.debug('Saved key: ' + key + ' for value: ' + value);
            }
        });
    }
};

init(this);


