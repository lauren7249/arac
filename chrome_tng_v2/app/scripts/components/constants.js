//############## CONSTANTS ###############
// Constants are not available within a
// class in ES6 at this time, so we're
// dropping them outside of the class definition.

/**
 * @constant Print extra debug to the browser console
 * @type {boolean}
 */
var AC_DEBUG_MODE = false;

/**
 * @constant Amazon region
 * @type {string}
 */
var AC_AWS_REGION = 'us-east-1';

/**
 * @constant AWS Bucket credentials
 * @type {string}
 */
var AC_AWS_CREDENTIALS = `${AC_AWS_REGION}:d963e11a-7c9b-4b98-8dfc-8b2a9d275574`;

/**
 * @constant S3 bucket name
 * @type {string}
 * @default chrome-ext-uploads
 */
var AC_AWS_BUCKET_NAME = 'chrome-ext-uploads';

// FIXME SHOULD BE HTTPS!
/**
 * @constant Base url for redis queue
 * @type {string}
 */
var AC_QUEUE_BASE_URL = 'http://169.55.28.212:8080';

/**
 * @constant Number of URLS retrieved at a time
 * @type {number}
 */
var AC_QUEUE_URLS_AT_A_TIME = 10;

/**
 * @constant Queue url, including query parameters
 * @type {string}
 */
var AC_QUEUE_URL = `${AC_QUEUE_BASE_URL}/select/n=${AC_QUEUE_URLS_AT_A_TIME}`;

/**
 * @constant Url to notify of successful scrape
 * @type {string}
 */
var AC_QUEUE_SUCCESS_URL_BASE = `${AC_QUEUE_BASE_URL}/post_uploaded`;

export { AC_AWS_BUCKET_NAME, AC_AWS_CREDENTIALS, AC_AWS_REGION, AC_DEBUG_MODE,
    AC_QUEUE_BASE_URL, AC_QUEUE_SUCCESS_URL_BASE, AC_QUEUE_URL };
