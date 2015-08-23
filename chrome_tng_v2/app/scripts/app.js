import React from 'react';
import './components/globals';
import AC_Helper from './components/globals';
import log from '../bower_components/log';
import URI from 'uri-js';

let Helper = AC_Helper();

/**
 * App is the outer container for the extension
 */
let App = React.createClass({
    getInitialState(){
        'use strict';
        return {
            queue: [],
            progress: 0
        };

    },
    render(){
        'use strict';
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

let QueryArea = React.createClass({
    render(){
        'use strict';
        return (
            <div className='scraper'>
                <Progress progress="0"/>
                <StatusArea />
            </div>
        );
    }
});

let Progress = React.createClass({
    render(){
        'use strict';
        return (
            <div></div>
        );
    }
});

let StatusArea = React.createClass({
    render(){
        'use strict';
        return (
            <div></div>
        );
    }
});

React.render(<App/>, document.body);
