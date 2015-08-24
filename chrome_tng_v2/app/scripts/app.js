import React from 'react';
import './components/helpers';
import AC_Helpers from './components/helpers';
import log from '../bower_components/log';
import { AC_AWS_BUCKET_NAME, AC_AWS_CREDENTIALS,
    AC_AWS_REGION,
    AC_DEBUG_MODE, AC_QUEUE_BASE_URL,
    AC_QUEUE_SUCCESS_URL_BASE, AC_QUEUE_URL } from './components/constants';

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
            this.getNextBatch(this);
        } else {
            this.componentDidMount();
        }
    },
    getNextBatch: function(ctx) {

        if (ctx !== undefined && ctx.isMounted()) {
            var _hp = ctx.props.hp || undefined;
            if (_hp !== undefined) {
                AC_Helpers.get_data(AC_QUEUE_URL,
                    undefined,
                    ctx.onNextBatchReceived,
                    ctx.onNetworkError);
            }
        } else {
            console.warn(`ctx not defined. ${ctx || undefined}`);
        }
    }.bind(),
    onNextBatchReceived: function(xhr, data) {
        var _hp = this.props.hp;
        _hp.debugLog(xhr);
        _hp.debugLog(data);
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

