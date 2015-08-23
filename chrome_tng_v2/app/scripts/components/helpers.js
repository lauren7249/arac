/**
 * Constants and Helper Functions
 */

/* eslint no-unused-vars:0 */

import qwest from 'qwest';
import log from '../../bower_components/log';
import URI from 'uri-js';
require('../../bower_components/aws-sdk-js/dist/aws-sdk.min.js');

//############## CONSTANTS ###############
// Constants are not available within a
// class in ES6 at this time, so we're
// dropping them outside of the class definition.

/**
 * @constant Print extra debug to the browser console
 * @type {boolean}
 */
const AC_DEBUG_MODE = true;

/**
 * @constant Amazon region
 * @type {string}
 */
const AC_AWS_REGION = 'us-east-1';

/**
 * @constant AWS Bucket credentials
 * @type {string}
 */
const AC_AWS_CREDENTIALS = `${AC_AWS_REGION}:d963e11a-7c9b-4b98-8dfc-8b2a9d275574`;

/**
 * @constant S3 bucket name
 * @type {string}
 * @default chrome-ext-uploads
 */
const AC_AWS_BUCKET_NAME = 'chrome-ext-uploads';

// FIXME SHOULD BE HTTPS!
/**
 * @constant Base url for redis queue
 * @type {string}
 */
const AC_QUEUE_BASE_URL = 'http://169.55.28.212:8080';

/**
 * @constant Number of URLS retrieved at a time
 * @type {number}
 */
const AC_QUEUE_URLS_AT_A_TIME = 100;

/**
 * @constant Queue url, including query parameters
 * @type {string}
 */
const AC_QUEUE_URL = `${AC_QUEUE_BASE_URL}/select/n=${AC_QUEUE_URLS_AT_A_TIME}`;

/**
 * @constant Url to notify of successful scrape
 * @type {string}
 */
const AC_QUEUE_SUCCESS_URL_BASE = `${AC_QUEUE_BASE_URL}/log_uploaded/url=`;

//########################################

/**
 * Helper functions and non-ui code.
 *
 * @author Michael Bishop
 *
 * @class
 */
export default class AC_Helpers {
    constructor() {
        'use strict';
        this._bucket = null;
        this.initAws();
        qwest.limit(5);
        qwest.setDefaultXdrResponseType('text/html');
        qwest.setRequestHeader('Accept-Language', 'en-US');
    }

    /**
     * @function Log message to browser console when
     * {AC_DEBUG_MODE} is true.
     * @static
     * @param {Object} obj
     */
    static debugLog(obj) {
        if (AC_DEBUG_MODE == true) {
            log('[c="color: blue"]DEBUG: `${obj}` [c]');
        }
    }

    /*global */
    static is_google(uri) {
        'use strict';
        let components = URI.parse(uri);
        debugLog(components);
        return (components.error == undefined
        && components.host
            .toLowerCase()
            .includes('google.com'));
    }

    /* eslint no-undef:0 */
    static google(url) {
        'use strict';
        debugLog('_is google_');
    }

    /**
     * Initialize the AWS Connection and instantiate
     * a handle to an S3 bucket.
     */
    initAws() {
        'use strict';
        try {
            AWS.config.region = AC_AWS_REGION;
            AWS.config.credentials = new AWS.CognitoIdentityCredentials({
                IdentityPoolId: AC_AWS_CREDENTIALS
            });
            this._bucket = new AWS.S3({
                params: {
                    Bucket: AC_AWS_BUCKET_NAME
                }
            });
        } catch (e) {
            log('Unable to conect to AWS: [c="color: red"]e[c]');
            this._bucket = undefined;
            throw e;
        }
    }

    /**
     * Get an AWS S3 bucket instance.  If the AWS
     * client has not already been initialized, calling
     * this method will do so.
     *
     * @returns {AWS.S3}
     */
    awsBucket() {
        'use strict';
        if (this._bucket != undefined) {
            return this._bucket;
        } else {
            this.initAws();
            return this.awsBucket();
        }
    }

    /**
     * Create a standardized uri
     * @param {string} old - uri to convert
     * @return {string} An https:// prefixed uri
     *
     * @see {@link http://medialize.github.io/URI.js/docs.html}
     */
    static standard_uri(old) {
        'use strict';
        let components = URI.parse(old);
        if (components.error == undefined) {

            components.scheme('https');
            return URI.serialize(components);

        } else {

            log('Unable to parse URI: [c="color: red"]_${old}_[c]');
            throw 'Unable to parse URI: [${old}]';
        }
    }

    /**
     * Generate an S3 key based off of the
     * original URL.  Replaces forward slashes (/)
     * with dashes (-).
     *
     * @param uri {string} uri - Base uri to convert into a key
     * @return {string} Formatted key for S3
     */
    static generate_s3_key(uri) {
        'use strict';
        return uri.replace('/\//g', '-')
            .concat('.html');
    }

    /**
     * Retrieves the contents of a url, accepting call-
     * back functions called once the call is complete.
     *
     * NOTE:  To make synchronous calls, you should use
     * the qwest library directly as this method does
     * not support use of the async:false option as
     * additional  logic would be required to handle
     * this case beyond changing the option.
     *
     * @static
     * @external "qwest.get"
     * @see {@link https://www.npmjs.com/package/qwest#quick-examples}
     * @param  {string} url - Url to call
     * @param {Object} [options] - A map of options to pass to qwest.get
     * @param {function} [fn_then] - Optional handler for success case. Expects a callback that accepts <strong>(xhr, response)</strong>.
     * @param {function} [fn_catch] - Optional handler for error case. Expects a callback that accepts <strong>(xhr, response, e)</strong>
     * @param {function} [fn_complete] - Optional handler that will always be called regardless of success or failure. Callback signature is <strong>(xhr, response)</strong>
     *
     * @see {@link https://www.npmjs.com/package/qwest#basics}
     */
    static get_url(url,
                   options = {
                       cache: false, timeout: 30000, async: true,
                       attempts: 1
                   },
                   fn_then = emptyFunction,
                   fn_catch = emptyFunction,
                   fn_complete = emptyFunction) {
        'use strict';
        let uri = URI.parse(url).toString();
        qwest.get(uri, null, options)
            .then(fn_then)
            .catch(fn_catch)
            .complete(fn_complete);

    }

    /**
     * Uploads to S3
     * @param {Object} params - {Key: keyname, ContentType: 'text/html', Body:content}
     * @param {function} [cb] Callback to execute on completion
     *
     * @external AWS#upload
     * @see {@link http://docs.aws.amazon.com/AWSJavaScriptSDK/latest/AWS/S3.html#upload-property}
     */
    upload_to_s3(params, cb = emptyFunction) {
        'use strict';
        assert(params.hasOwnProperty('Key') && params.hasOwnProperty('Body'));

        this.awsBucket().upload(params, function(err, data) {
            if (err) {
                log(err.toString);
            }
            cb(err, data);
        });
    }

    /**
     * Notify AC that a successful scrape has completed
     * and the result is loaded into S3.
     *
     * @param {string} uri - URI scraped
     *
     * TODO Review the regex replacement to see if we can accomplish the same in a less brittle way
     * @see {@link http://medialize.github.io/URI.js/docs.html#iso8859}
     */
    static notify_s3_success(uri) {
        'use strict';

        let orig_url = URI.parse(uri).toString();
        assert(orig_url.error == undefined);

        orig_url = orig_url.replace('/\//g', ';').replace('/\?/g', '`');
        let notification_url = AC_QUEUE_SUCCESS_URL_BASE.concat(orig_url);

        get_url(notification_url, undefined,
            (xhr, response) => {
                debugLog(`SUCCESS: ${notification_url}`);
            },
            (xhr, response, e) => {
                log(`FAILURE: ${notification_url} [${e.toString}]`);
            });
    }

}
