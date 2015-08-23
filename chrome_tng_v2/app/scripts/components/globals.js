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
const AC_DEBUG_MODE = true;

const AC_AWS_REGION = 'us-east-1';
const AC_AWS_CREDENTIALS = `${AC_AWS_REGION}:d963e11a-7c9b-4b98-8dfc-8b2a9d275574`;
const AC_AWS_BUCKET_NAME = 'chrome-ext-uploads';

// FIXME SHOULD BE HTTPS!
const AC_QUEUE_BASE_URL = 'http://169.55.28.212:8080';
const AC_QUEUE_URLS_AT_A_TIME = 100;
const AC_QUEUE_URL = `${AC_QUEUE_BASE_URL}/select/n=${AC_QUEUE_URLS_AT_A_TIME}`;
const AC_QUEUE_SUCCESS_URL_BASE = `${AC_QUEUE_BASE_URL}/log_uploaded/url=`;

//########################################

/**
 * Helper functions and non-ui
 * code.
 */
export default class AC_Helpers {
    constructor() {
        'use strict';
        this._bucket = null;
        this.initAws();
        qwest.limit(5);
        qwest.setDefaultXdrResponseType('text/html');
        qwest.setRequestHeader('Accept-Language','en-US');
    }

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
     * @param old uri
     * @return An https:// prefixed uri
     */
    static standard_uri(old) {
        'use strict';
        let components = URI.parse(old);
        if (components.error == undefined) {

            components.scheme = 'https';
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
     * @param uri
     * @return {string} Formatted key for S3
     */
    static generate_s3_key(uri) {
        'use strict';
        return uri.replace('/\//g', '-')
            .concat('.html');
    }

    static get_url(url, data,
                   options = {
                       cache: false, timeout: 30000, async: true,
                       attempts: 1
                   },
                   fn_then = emptyFunction,
                   fn_catch = emptyFunction,
                   fn_complete = emptyFunction) {
        'use strict';
        qwest.get(url, data, options)
            .then(fn_then)
            .catch(fn_catch)
            .complete(fn_complete);

    }

}
