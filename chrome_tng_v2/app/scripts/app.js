import React from 'react';
import qwest from 'qwest';
import './components/helpers';
import AC_Helpers from './components/helpers';
import log from '../bower_components/log';
import { AC_AWS_BUCKET_NAME, AC_AWS_CREDENTIALS,
    AC_AWS_REGION,
    AC_DEBUG_MODE, AC_QUEUE_BASE_URL,
    AC_QUEUE_SUCCESS_URL_BASE, AC_QUEUE_URL } from './components/constants';
import {urls as test_urls} from './components/regular_urls';
import Immutable from 'immutable';

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

var http_options = {
    cache: false, timeout: 30000, async: true,
    attempts: 1, headers: {
        'Accept-Language': 'en-US'
    }
};
qwest.limit(1);
qwest.setDefaultXdrResponseType('text');


var TimerMixin = require('react-timer-mixin');

var SetIntervalMixin = {
    componentWillMount: function() {
        this.intervals = [];
    },
    setInterval: function() {
        this.intervals.push(setInterval.apply(null, arguments));
    },
    componentWillUnmount: function() {
        this.intervals.map(clearInterval);
    }
};

var App = React.createClass({
    mixins: [TimerMixin, SetIntervalMixin],
    getInitialState: function() {
        return {
            queue: Immutable.Stack(),
            progress: 0,
            progress_val: 0,
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
        console || console.assert(_hp != undefined,
            'Helper is not defined');
    },
    componentDidMount: function() {
        var that = this;
        if (this && this.isMounted()) {
            //this.getNextBatchOfTestURLS(this);
            that.getNextBatch();
            that.setInterval(that.onCheckForWork, 30000);
        } else {
            this.componentDidMount();
        }
    },
    getNextBatchOfTestURLS: function(ctx) {
        // Only used in TEST
        var promise = new Promise(function(resolve, reject) {
            resolve(test_urls);
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
                        queue: that.state.queue.unshift(item)
                    };
                });
            }
        });
        that.onCheckForWork();
    },
    /**
     * @private
     * @param {string} url
     * @param {boolean} in_use
     */
    setUrlInUse(url, in_use){
        return undefined;
    },
    onWorkTaken(url){
        qwest.get(url, null, http_options)
            .then(this.onScrapeSucceeded)
            .catch(this.onScrapeFailed);
    },
    /**
     * Called after scrape task has completed.
     *
     * @param {string} url - URL that had been scraped
     * @param {boolean} success - Success/Failure of scrape
     * @param {XMLHttpRequest} ctx - Context object
     */
    onWorkFinished(url, success, ctx){
        this.setState((state, props)=> {
            return ({
                progress_val: state.progress_val + 1
            });
        });
        this.onCheckForWork();
    },
    onNetworkError: function(xhr, data, err) {
        console || console.error(`${xhr} ${data} ${err}`);
    },
    /**
     *
     * @param {SyntheticEvent} e
     */
    onCheckForWork: function(e) {
        var that = this;

        if (e !== undefined) {
            if (e.currentTarget.name === 'scrape_it') {
                that.getNextBatch();
            }
        }
        /**
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
                    that.getRandomInt(1, 5)
                );
            });
        } else {
            that.getNextBatch();
        }
    },
    onScrapeSucceeded: function(xhr, data) {
        console.debug(`[${xhr.status}] [${xhr.statusText}] [${xhr.responseURL}]`);
        this.onScrapeDoneAlwaysDo(xhr, data);
    },
    onScrapePageNotFound: function(xhr, data) {
        window.alert('Page not found.');
    },
    /**
     *
     * @param  {XMLHttpRequest} xhr
     * @param data
     * @param err
     */
    onScrapeFailed: function(xhr, data, err) {
        console.error(err);
        this.onScrapeDoneAlwaysDo(xhr, data);
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
     */
    onScrapeDoneAlwaysDo: function(xhr, response) {
        if (AC_Helpers.is_empty(xhr)) {
            return;
        }
        let _hp = this.props.hp;
        let _url = xhr.responseURL;
        let s3_parms = {
            Key: AC_Helpers.generate_s3_key(_url),
            Body: response, ContentType: html_mime
        };
        var that = this;
        _hp.upload_to_s3(s3_parms, function(err, data) {
            console.log(data);
            if (captcha.test(response) === true) {
                console.error(`CAPTCHA DETECTED! [${xhr.responseURL}]`);
                window.open(xhr.responseURL, 'AC_C');
            }
            that.onWorkFinished(xhr.responseURL, true);
        });
    },
    render: function() {
        /*        let _rows = this.state.queue.map((row, idx)=> {
         if (idx > 10) {
         return undefined;
         }
         return (
         <tr key={'tr-'+ idx}>
         <td key={'td-' + idx}>
         {idx}
         </td>
         </tr>
         );
         }, this);*/
        return (
            <div>
                <div className='hero-unit'>
                    <p>AC Browser</p>

                    <div className='scrape_list'/>
                    <progress value={this.state.progress_val}
                              max={this.state.queue.size}
                              className='scrape_progress'/>
                    <br />
                    <dialog>TEST</dialog>
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

React.render(<App />, document.getElementById('App'));

