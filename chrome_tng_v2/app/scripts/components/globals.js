/**
 * Constants and Helper Functions
 */

/* eslint no-unused-vars:0 */

import log from '../../bower_components/log';
require('../../bower_components/aws-sdk-js/dist/aws-sdk.min.js');

const AC_AWS_REGION = 'us-east-1';
const AC_AWS_CREDENTIALS = `${AC_AWS_REGION}:d963e11a-7c9b-4b98-8dfc-8b2a9d275574`;
const AC_AWS_BUCKET_NAME = 'chrome-ext-uploads';

// FIXME SHOULD BE HTTPS!
const AC_QUEUE_BASE_URL = 'http://169.55.28.212:8080';
const AC_QUEUE_URLS_AT_A_TIME = 100;
const AC_QUEUE_URL = `${AC_QUEUE_BASE_URL}/select/n=${AC_QUEUE_URLS_AT_A_TIME}`;
const AC_QUEUE_SUCCESS_URL_BASE = `${AC_QUEUE_BASE_URL}/log_uploaded/url=`;

/**
 * Helper functions and non-ui
 * code
 */
export default class AC_Helpers {
    constructor() {
        'use strict';
        this._bucket = null;
        this.initAws();
    }

    /*global */
    static is_google(url) {
        'use strict';
        return url.match(/www.google.com/g, url) != null;
    }

    /* eslint no-undef:0 */
    static google(url) {
        'use strict';
        log('_is google_');
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

}
