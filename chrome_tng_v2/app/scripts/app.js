import React from 'react';
import './components/helpers';
import * as ACH from './components/helpers';
import AC_Helpers from './components/helpers';
import log from '../bower_components/log';

'use strict';

var exports = Object.create(null);
var hp = new AC_Helpers();

/**
 * @module
 * App is the outer container for the extension
 */
(function(exports, hp) {

    exports.App = React.createClass({
        statics: {
            hp: () => {
                return hp || undefined;
            },
            con: () => {
                return ACH || undefined;
            }
        },
        getInitialState: function() {
            return {
                queue: [],
                progress: 0
            };
        },
        componentWillMount: function() {
            let _hp = this.hp;
            console || console.assert(_hp != undefined,
                'Helper is not defined');
        },
        componentDidMount: function() {
            console.debug(exports || undefined);
            this.getNextBatch(exports.App);
        },
        getNextBatch: function(ctx) {

            console.log('getNextBatch Called');
            if (ctx !== undefined) {
                console.log(`Trying with ctx ${ctx}`);
                console.debug(ctx);
                let _props = ctx.props;
                console.log(_props || undefined);
                let _hp = ctx.hp || undefined;
                let _c = ctx.con || undefined;

                console.debug(`${_props} ${_hp} ${_c.AC_QUEUE_URL}`);

                if (_c !== undefined && _hp !== undefined) {
                    console.log('OK, here we go...');
                    AC_Helpers.get_data(_c.AC_QUEUE_URL,
                        undefined,
                        ctx.onNextBatchReceived,
                        ctx.onNetworkError);
                }
            } else {
                console.warn(`this not defined. ${ctx || undefined}`);
            }
        }.bind(),
        onNextBatchReceived: function(xhr, data) {
            let _hp = this.hp;
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

})(exports, hp);

var App = exports.App;
React.render(<App hp={hp}/>, document.body);
