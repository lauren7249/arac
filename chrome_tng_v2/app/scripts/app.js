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
        AC_Helpers.get_data(
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
        data.forEach((item) => {

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
        });
        this.onCheckForWork();
    },
    /**
     * @private
     * @param {string} url
     * @param {boolean} in_use
     */
    setUrlInUse(url, in_use){
        this.setState((state, props) => {
            let _queue = state.queue;
            if (_queue[url] === true) {
                return _queue = _queue.delete(url);
            } else {
                return _queue.set(url, in_use);
            }
        }, (in_use) => {
            if (in_use === false) {
                this.onCheckForWork();
            }
        });
    },
    onWorkTaken(url){
        console.debug(url);
        this.setUrlInUse(url, true);
        AC_Helpers.get_data(url, undefined,
            this.onScrapeSucceeded,
            this.onScrapeFailed,
            this.onScrapeDoneChecker);
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
        this.setUrlInUse(url, false);
    },
    onNetworkError: function(xhr, data, err) {
        console || console.error(`${xhr} ${data} ${err}`);
    },
    /**
     *
     * @param {SyntheticEvent} e
     */
    onCheckForWork: function(e) {
        if (e.currentTarget.name === 'scrape_it') {

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
        _available_work.forEach((in_use, url) => {
            this.setTimeout(
                () => {
                    this.onWorkTaken(url);
                },
                this.getRandomInt(1, 5)
            );
        }, this);
    },
    onScrapeSucceeded: function(xhr, data) {
        console.debug(`[${xhr.status}] [${xhr.statusText}] [${xhr.responseURL}]`);
        this.onWorkFinished(xhr.responseURL, true);
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
        console.error(xhr);
        window.open(xhr.responseURL, 'AC_F');
        this.onWorkFinished(xhr.responseURL, false);
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
    onScrapeDoneChecker: function(xhr, response) {
        if (captcha.test(response) === true) {
            console.error(`CAPTCHA DETECTED! [${xhr.responseURL}]`);
            window.open(xhr.responseURL, 'AC_C');
        }
        this.setTimeout(
            () => {
                this.setUrlInUse(xhr.responseURL, false);
            }, this.getRandomInt(1, 5)
        );
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

