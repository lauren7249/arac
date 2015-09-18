/**
 * Created by mbishop on 9/17/15.
 */

import {console, AC_Helpers} from './components/helpers';
import { kUid_key } from './components/constants';

var React = require('react');
var Immutable = require('immutable');
/**
 * @module
 * App is the outer container for the extension
 */
'use strict';

var ACOptions = React.createClass({
    getInitialState: ()=> {
        return {

        };
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


React.render(<ACOptions />, document.getElementById('ACOptions'));
