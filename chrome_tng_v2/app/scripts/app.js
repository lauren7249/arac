import React from 'react';
import './components/helpers';
import AC_Helpers from './components/helpers';
import log from '../bower_components/log';
import { AC_AWS_BUCKET_NAME, AC_AWS_CREDENTIALS,
    AC_AWS_REGION,
    AC_DEBUG_MODE, AC_QUEUE_BASE_URL,
    AC_QUEUE_SUCCESS_URL_BASE, AC_QUEUE_URL } from './components/constants';
import {urls as test_urls} from './components/regular_urls';

'use strict';

/**
 * @module
 * App is the outer container for the extension
 */
'use strict';

var App = React.createClass({
    getInitialState: function() {
        return {
            queue: [],
            progress: 0
        };
    },
    getDefaultProps: function() {
        return {
            hp: new AC_Helpers()
        };
    },
    componentWillMount: function() {
        var _hp = this.props.hp;
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
            let urls = test_urls.split('\n');
            resolve(urls);
        });
        promise.then(function(urls) {
            ctx.onNextBatchReceived(undefined, urls);
        });
    }.bind(),
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

    }.bind(),
    /**
     * Chunks arrive as newline delimited url
     * strings and should be transformed into
     * a list before processing further.
     */
    onNextBatchReceived: function(xhr, data) {
        console || console.assert(AC_Helpers.is_iterable(data));
        data.forEach((item) => {
            console.log(`Rec'd: ${item}`);
        });
    }.bind(),
    onNetworkError: function(xhr, data, err) {
        console || console.error(`${xhr} ${data} ${err}`);
    }.bind(),
    render: function() {
        return (
            <div>
                <div className='hero-unit'>
                    <p>AC Browser</p>
                    <QueryArea />
                </div>
            </div>
        );
    }
});

var QueryArea = React.createClass({
    getInitialState: function() {
        return {
            value: 0,
            max: 100
        };
    },
    render: function() {
        return (
            <div className='scraper'>
                <progress value="0" max="100" width="100%"/>
                <StatusArea />
            </div>
        );
    }
});


var StatusArea = React.createClass({
    render: function() {
        return (
            <table width="80%">

            </table>
        );
    }
});


export{ App };

React.render(<App />, document.getElementById('App'));

