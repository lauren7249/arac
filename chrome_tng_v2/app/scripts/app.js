//import AC_Helpers from './components/helpers';
import { AC_AWS_BUCKET_NAME, AC_AWS_CREDENTIALS,
    AC_AWS_REGION,
    AC_DEBUG_MODE, AC_QUEUE_BASE_URL,
    AC_QUEUE_SUCCESS_URL_BASE, AC_QUEUE_URL } from './components/constants';
//import {urls as test_urls} from './components/regular_urls';
import {console, AC_Helpers} from './components/helpers';

var React = require('react');
var Immutable = require('immutable');
/**
 * @module
 * App is the outer container for the extension
 */
'use strict';

/**
 * Pre-compile Regex for performance
 * @type {RegExp}
 */
var captcha = /captcha/i;

var html_mime = 'text/html';

/**
 * Default HTTP Options passed
 */
var http_options = {
    cache: false, timeout: 30000, async: true,
    attempts: 1, headers: {
        'Accept-Language': 'en-US'
    }
};
// Seal the options_object
Object.seal(http_options);
/**
 * Set a limit of 1 HTTP request at a time.  Note
 * this is less than a web browser which can normally
 * make 5 simultaneous requests per domain name
 */
var qwest = require('qwest');
qwest.limit(1);
qwest.setDefaultXdrResponseType('text');


var TimerMixin = require('react-timer-mixin');

/**
 * App is the main component and new
 * HTML element <App />
 */
var App = React.createClass({
    mixins: [TimerMixin],
    getInitialState: function() {
        return {
            queue: Immutable.Stack(),
            click_enabled: true,
            meter_now: 0,
            meter_max: 0,
            last_scrape: Date.now()
        };
    },
    getDefaultProps: function() {
        return {
            hp: new AC_Helpers()
        };
    },
    componentWillMount: function() {
        let _hp = this.props.hp;
        console && console.assert(_hp != undefined,
            'Helper is not defined');
    },
    componentDidMount: function() {
        var that = this;
        if (this && this.isMounted()) {
            //this.getNextBatchOfTestURLS(this);
            that.getNextBatch();
            that.setInterval(that.onCheckForWork, 300000);
        } else {
            this.componentDidMount();
        }
    },
    getNextBatchOfTestURLS: function(ctx) {
        // Only used in TEST
        var promise = new Promise(function(resolve, reject) {
            //resolve(test_urls);
            resolve([]);
        });
        promise.then(function(urls) {
            ctx.onNextBatchReceived(undefined, urls);
        });
    },
    /**
     * Retrieve a new batch of URLS from Redis.
     * Data arrives a single data chunk of newline
     * delimited url strings.
     */
    getNextBatch: function() {
        qwest.get(AC_QUEUE_URL, null, http_options)
            .then(this.onNextBatchReceived)
            .catch(this.onNetworkError);
    },
    /**
     * Return a random integer between min and max,
     * inclusive
     */
    getRandomInt(min, max){
        return Math.floor(Math.random() * (max - min)) + min;
    },
    /**
     * Chunks arrive as newline delimited url
     * strings and should be transformed into
     * a list before processing further.
     */
    onNextBatchReceived: function(xhr, data) {
        data = AC_Helpers.delimited_to_list(data, '\n');
        var that = this;
        data.forEach(function(item) {
            // Check if the component has been mounted onto
            // the DOM before mutating state.
            if (that.isMounted()) {
                that.setState((state, props) => {
                    var _item = AC_Helpers.normalize_string(item);
                    return {
                        queue: that.state.queue.unshift(_item)
                    };
                });
            }
        });
        that.onCheckForWork();
    },
    /**
     * Called when a Scrape job has been assigned
     * This kicks off the worker.
     *
     * @param {strong} url - The url to scrape
     */
    onWorkTaken(url){
        var that = this;
        qwest.get(url, null, http_options)
            .then(function(xhr, data) {
                that.onScrapeSucceeded(xhr, data, url);
            })
            .catch(function(xhr, data, error) {
                that.onScrapeFailed(xhr, data, error, url);
            });
    },
    /**
     * Called after scrape task has completed.
     *
     * @param {string} url - URL that had been scraped
     * @param {boolean} success - Success/Failure of scrape
     */
    onWorkFinished(url, success){
        /**
         * The boundary of work was changed during development
         *  and the bulk of the code initially envisioned is now
         *  in onScrapeSucceeded.  This fragment is left in place
         *  as a logical extension point for retry logic.
         */

        this.onCheckForWork();
    },
    onNetworkError: function(xhr, data, err) {
        console && console.error(`${xhr} ${data} ${err}`);
    },
    /**
     * Called when button is clicked, when the queue
     * is drained and from a slow timer to attempt
     * to keep the queue full in all cases.
     *
     * @param {SyntheticEvent} e
     */
    onCheckForWork: function(e) {
        var that = this;

        if (e !== undefined) {
            // The eventSource was the Get More Work Button
            if (e.currentTarget.name === 'scrape_it') {
                that.setState(
                    {
                        click_enabled: false // TODO Re-enable button when queue is empty
                    }
                );
                that.getNextBatch();
            }
        }
        /**
         * Type information to help IDE do code completion
         * @type {Immutable.Stack}
         * @private
         */
        let _queue = that.state.queue;
        var _item = undefined;
        if (_queue.peek() !== undefined) {
            that.setState(function(state, props) {
                _item = state.queue.first();
                return {
                    queue: state.queue.shift()
                };
            }, function() {
                that.setTimeout(
                    function() {
                        that.onWorkTaken(_item);
                    },
                    that.getRandomInt(5, 30)
                );
            });
        } else {
            that.getNextBatch();
        }
    },
    onScrapeSucceeded: function(xhr, data, original_url) {
        //console.debug(`[${xhr.status}] [${xhr.statusText}] [${original_url}]`);
        this.onScrapeDoneAlwaysDo(xhr, data, original_url);
    },
    onScrapePageNotFound: function(xhr, data, original_url) {
        console && console.error(`Page not found. [${original_url}]`);
    },
    /**
     *
     * @param  {XMLHttpRequest} xhr
     * @param data
     * @param err
     * @param {string} original_url
     */
    onScrapeFailed: function(xhr, data, err, original_url) {
        console && console.warn(err);
        this.onScrapeDoneAlwaysDo(xhr, data, original_url);
        //window.open(xhr.responseURL, 'AC_F');
    },
    /**
     * Callback that can inspect responses that
     * have been marked as either success or failed.
     *
     * New detection testing code can go here.
     *
     * @param {XMLHttpRequest} xhr
     * @param response
     * @param {string} original_url
     */
    onScrapeDoneAlwaysDo: function(xhr, response, original_url) {
        xhr && xhr.isPrototypeOf(XMLHttpRequest);
        var _hp = this.props.hp;

        let s3_parms = {
            Key: AC_Helpers.generate_s3_key(original_url),
            Body: response, ContentType: html_mime
        };

        var that = this;
        _hp.upload_to_s3(s3_parms, function(err, data) {
            if (data !== undefined) {
                _hp.notify_s3_success(original_url);
            }
            if (captcha.test(response) === true) {
                console.warn(`CAPTCHA DETECTED! [${original_url}]`);
                //window.open(xhr.responseURL, 'AC_C');
            }
            that.onWorkFinished(original_url, true);
        });
    },
    render: function() {
        return (
            <div>
                <div className='hero-unit'>
                    <p>AC Browser</p>

                    <div className='scrape_list'/>
                    <div className='queue_size_container'>
                        <p >
                            <computercode className='queue_size'>
                                {this.state.queue.count()}
                            </computercode>
                        </p>
                    </div>
                    <br />
                    <button type='button' name='scrape_it' key='work'
                            enabled={this.state.click_enabled}
                            width='100%' onClick={this.onCheckForWork}>
                        Get New Work
                    </button>
                </div>
            </div>
        );
    }
});


export{ App };


//React.render(<App />, document.getElementById('App'));


