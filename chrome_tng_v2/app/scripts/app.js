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
(function(exports) {

    console.debug(exports || undefined);

    exports.App = React.createClass({
        getDefaultProps: function() {
            return {
                hp: undefined
            };
        },
        getInitialState: function() {
            return {
                queue: [],
                progress: 0
            };
        },
        componentWillMount: function() {

        },
        componentDidMount: function() {
            this.getNextBatch();
        },
        getNextBatch: function() {
            let _hp = this.props.hp;
            _hp.get_next_batch();
        },
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
                progress: 0
            };
        },
        render: function() {
            return (
                <div className='scraper'>
                    <progress progress="0"/>
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

})(exports);

console.debug(exports);
console.debug(ACH);


var App = exports.App;

React.render(<App hp={hp}/>, document.body);
