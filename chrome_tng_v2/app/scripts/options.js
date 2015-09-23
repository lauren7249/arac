/**
 * Created by Michael Bishop on 9/17/15.
 * (c) Advisor Connect, Inc. 2015
 */

import {console, AC_Helpers} from './components/helpers';
import { kUid_key } from './components/constants';

var React = require('react');
var Immutable = require('immutable');
/**
 * @module
 * ACOptions is the outer container for the extension
 */
'use strict';

var ACOptions = React.createClass({
    getInitialState: ()=> {
        return {};
    },
    getDefaultProps: ()=> {
        return {
            hp: new AC_Helpers()
        };
    },
    componentWillMount: function() {
        let _hp = this.props.hp;
        console && console.assert(_hp != undefined,
            'Helper is not defined');
    },
    render: function() {
        let _user = localStorage && localStorage.getItem(kUid_key) || 'Not Available';
        return (
            <div>
                <p>
                    Support Token: &nbsp; <span><code>{_user}</code></span>
                </p>
            </div>
        );
    }
});

export { ACOptions };


/**
 * Need to have this in try/catch.  When bundled, this code should only
 * get called if the options.html page is actually on-screen and the dom
 * element is there.
 */
try {
    let element = document && document.getElementById('ACOptions');
    if (element) {
        React.render(<ACOptions />, document.getElementById('ACOptions'));
    }
} catch (e) {
    console.error(e);
}
