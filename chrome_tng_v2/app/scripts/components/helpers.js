/**
 * Constants and Helper Functions
 */

/* eslint no-unused-vars:0 */

import qwest from 'qwest';
import log from '../../bower_components/log';
import URI from 'uri-js';
import { AC_AWS_BUCKET_NAME, AC_AWS_CREDENTIALS,
    AC_AWS_REGION,
    AC_DEBUG_MODE, AC_QUEUE_BASE_URL,
    AC_QUEUE_SUCCESS_URL_BASE, AC_QUEUE_URL } from 'constants';

/**
 * Helper functions and non-ui code.
 *
 * @author Michael Bishop
 *
 * @class
 */
export default class AC_Helpers extends Object {
    constructor() {
        'use strict';
        super();
        this.AWS = AWS;
        this._bucket = undefined;
        this.initAws();
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
    /**
     * @static
     * @param uri
     * @return {boolean}
     */
    static is_google(uri) {
        'use strict';
        var components = URI.parse(uri);
        AC_Helpers.debugLog(components);
        return (components.error == undefined
        && components.host
            .toLowerCase()
            .includes('google.com'));
    }

    /* eslint no-undef:0 */
    /**
     * @static
     * @param url
     */
    static google(url) {
        'use strict';
        AC_Helpers.debugLog('_is google_');
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
            log(`Unable to conect to AWS: [c="color: red"]${e}[c]`);
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
     *
     * @static
     * @param {string} old - uri to convert
     * @return {string} An https:// prefixed uri
     *
     * @see {@link http://medialize.github.io/URI.js/docs.html}
     */
    static standard_uri(old) {
        'use strict';
        var components = URI.parse(old);
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
    static get_data(url,
                    options = {
                        cache: false, timeout: 30000, async: true,
                        attempts: 1, headers: {
                            'Accept-Language': 'en-US'
                        }
                    },
                    fn_then = undefined,
                    fn_catch = undefined,
                    fn_complete = undefined) {
        'use strict';

        AC_Helpers.debugLog(`get_data called for ${url}`);

        var uri = AC_Helpers.get_valid_uri(url);
        if (uri != undefined) {

            qwest.limit(5);
            qwest.setDefaultXdrResponseType('text');

            qwest.get(uri, null, options)
                .then(fn_then)
                .catch(fn_catch)
                .complete(fn_complete);
        } else {
            throw `Invalid url passed ${url} to get_data`;
        }
    }

    /**
     * Returns a correctly formatted URI
     * or undefined if unable to parse
     *
     * @static
     * @param {string} uri to validate
     * @return {string|undefined}
     */
    static get_valid_uri(uri) {
        'use strict';
        var _uri = URI.parse(uri);
        return URI.serialize(_uri) || undefined;
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
     * @static
     * @param {string} uri - URI scraped
     *
     * TODO Review the regex replacement to see if we can accomplish the same in a less brittle way
     * @see {@link http://medialize.github.io/URI.js/docs.html#iso8859}
     */
    static notify_s3_success(uri) {
        'use strict';

        var orig_url = URI.parse(uri).toString();
        assert(orig_url.error == undefined);

        orig_url = orig_url.replace('/\//g', ';').replace('/\?/g', '`');
        var notification_url = AC_QUEUE_SUCCESS_URL_BASE.concat(orig_url);

        get_data(notification_url, undefined,
            (xhr, response) => {
                AC_Helpers.debugLog(`SUCCESS: ${notification_url}`);
            },
            (xhr, response, e) => {
                log(`FAILURE: ${notification_url} [${e.toString}]`);
            });
    }

    /**
     * @static
     * @param obj
     * @return {boolean}
     */
    static is_iterable(obj) {
        'use strict';
        if (obj === undefined || obj === null) {
            return false;
        } else {
            return obj.iterator !== undefined;
        }
    }

    /**
     * @static
     * @param obj
     * @return {boolean}
     */
    static is_empty_list(obj) {
        'use strict';
        if (obj === undefined || obj === null ||
            obj.length === 0) {
            return true;
        }
    }

    /**
     * Takes in a delimited blob of test and returns
     * a list. This is intended only to be used on single
     * column text objects.
     *
     * Passing in an iterable object will result in
     * the same object being returned.
     *
     * TODO Make this more robust to formats beyond \n delimited
     *
     * @param {string} text blob to convert
     * @param {string} delimiter to demarcate the end of line
     */
    static delimited_to_list(text, delimiter = '\n') {
        'use strict';
        if (AC_Helpers.is_empty_list(text)) {
            console.warn(`Empty value ${text}: returning []`);
            return [];
        } else if (AC_Helpers.is_iterable(text)) {
            return text;
        }
        return [text.join(delimiter)];
    }

}
