import React from 'react';
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

var TimerMixin = require('react-timer-mixin');

var App = React.createClass({
    mixins: [TimerMixin],
    getInitialState: function() {
        return {
            queue: Immutable.Map({}),
            progress: 0,
            progress_val: 0,
            last_scrape: new Date()
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
        if (this && this.isMounted()) {
            //this.getNextBatchOfTestURLS(this);
            this.getNextBatch(this);
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
    getNextBatch: function(ctx) {
        this.props.hp.get_data(
            AC_QUEUE_URL,
            undefined,
            ctx.onNextBatchReceived,
            ctx.onNetworkError);
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
        data.forEach(function(item) {

            // Check if the component has been mounted onto
            // the DOM before mutating state.
            if (this.isMounted()) {
                this.setState((state, props) => {
                    var _item = AC_Helpers.normalize_string(item);
                    /**
                     *
                     * @type {Immutable.Map}
                     * @private
                     */
                    let _queue = state.queue;
                    if (!_queue.get(_item)) {
                        var _newQ = _queue.set(_item, false);
                    }
                    return {
                        queue: _newQ
                    };
                });
            }
        }, this);
        this.onCheckForWork();
    },
    /**
     * @private
     * @param {string} url
     * @param {boolean} in_use
     */
        setUrlInUse(url, in_use){
        var _in_use = in_use;
        this.setState(function(state, props) {
            let _queue = state.queue;
            if (_queue[url] === true) {
                return _queue = _queue.delete(url);
            } else {
                return _queue.set(url, _in_use);
            }
        });
        if (_in_use === false) {
            console.debug('Calling onCheckForWork');
            this.onCheckForWork();
        } else {
            console.log(`IN_USE [${_in_use}]`);
        }
    },
    onWorkTaken(url){
        console.debug(url);
        this.setUrlInUse(url, true);
        this.props.hp.get_data(url, undefined,
            this.onScrapeSucceeded,
            this.onScrapeFailed,
            this.onScrapeDoneAlwaysDo);
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
    },
    onNetworkError: function(xhr, data, err) {
        console || console.error(`${xhr} ${data} ${err}`);
    },
    /**
     *
     * @param {SyntheticEvent} e
     */
    onCheckForWork: function(e) {
        if (e !== undefined) {
            if (e.currentTarget.name === 'scrape_it') {

            }
        }
        /**
         * @type {Immutable.Map}
         * @private
         */
        let _queue = this.state.queue;
        /**
         * Return the first 5 work items
         * not currently being scraped.
         *
         * @type {Iterable}
         */
        let _available_work = _queue
            .filter(inuse => inuse === false)
            .take(2);
        _available_work.forEach(function(in_use, url) {
            //this.setTimeout(
            //    function() {
            console.debug(new Date().getTime().toString());
            this.onWorkTaken(url);
            //},
            //this.getRandomInt(1, 5)
            //);
        }, this);
    },
    onScrapeSucceeded: function(xhr, data) {
        console.log('Success');
        console.debug(`[${xhr.status}] [${xhr.statusText}] [${xhr.responseURL}]`);
        /**
         * This callback is not being triggered
         * by qwest, it looks like the object is being
         * garbage collected before it can hit the method
         * so just going to call it imperatively.
         */
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
        xhr || console.warn(`Failed: ${xhr}}`);
        err || console.warn(`Err: [${err}}]`);
        xhr || window.open(xhr.responseURL, 'AC_F');
        /**
         * This callback is not being triggered
         * by qwest, it looks like the object is being
         * garbage collected before it can hit the method
         * so just going to call it imperatively.
         */
        xhr || this.onScrapeDoneAlwaysDo(xhr, data);
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
            console.log(`xhr is [${xhr}] response is [${response}]`);
            return;
        }
        var _url = xhr.responseURL;
        var s3_parms = {
            Key: AC_Helpers.generate_s3_key(_url),
            Body: response, ContentType: html_mime
        };

        console.log(`Upload requested: [${s3_parms}]`);
        var _strong = this.props.hp.upload_to_s3(s3_parms, function(err, data) {
            console.debug(data);
            if (captcha.test(response) === true) {
                console.error(`CAPTCHA DETECTED! [${xhr.responseURL}]`);
                window.open(xhr.responseURL, 'AC_C');
            }
            //this.setTimeout(
            //    function() {
            console.debug(new Date().getTime().toString());
            this.onWorkFinished(xhr.responseURL, true);
            this.setUrlInUse(xhr.responseURL, false);
            //}, this.getRandomInt(1, 5)
            //);
        }, this);
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

