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

'use strict';

/**
 * @module
 * App is the outer container for the extension
 */
'use strict';
//var update = require('react/addons').addons.update;

var App = React.createClass({
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
            this.getNextBatchOfTestURLS(this);
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
                    let _queue = this.state.queue;
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
    onWorkTaken(url){
        console.debug(url);
        // TODO Set in_use state = true
        AC_Helpers.get_data(url, undefined,
            this.onScrapeSucceeded,
            this.onScrapeFailed);
    },
    /**
     * Called after scrape task has completed.
     *
     * @param {string} url - URL that had been scraped
     * @param {boolean} success - Success/Failure of scrape
     * @param {XMLHttpRequest} ctx - Context object
     */
    onWorkFinished(url, success, ctx){

    },
    onNetworkError: function(xhr, data, err) {
        console || console.error(`${xhr} ${data} ${err}`);
    },
    onCheckForWork: function(e) {
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
            .take(5);
        _available_work.forEach((in_use, url) => {
            this.onWorkTaken(url);
        }, this);
    },
    onScrapeSucceeded: function(xhr, data) {
        console.debug(xhr);
        this.onWorkFinished(xhr.responseURL, true);
    },
    /**
     *
     * @param  {XMLHttpRequest} xhr
     * @param data
     * @param err
     */
    onScrapeFailed: function(xhr, data, err) {
        console.error(err);
        console.error(xhr);
        this.onWorkFinished(xhr.responseURL, false);
    },
    render: function() {
        //let _rows = this.state.queue.map((row, idx)=> {
        //    if (idx > 10) {
        //        return undefined;
        //    }
        //    return (
        //        <tr key={'tr-'+ idx}>
        //            <td key={'td-' + idx}>
        //                {idx}
        //            </td>
        //        </tr>
        //    );
        //}, this);
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
                    <button type='button' name='scrape_it'
                            width='100%'>Get New Work
                    </button>
                </div>
            </div>
        );
    }
});


export{ App };

React.render(<App />, document.getElementById('App'));

