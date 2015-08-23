import React from 'react';
import QueryArea from 'queryarea';

/**
 * Deprecated
 */
export default class extends React.Component {
    constructor(props) {
        'use strict';
        super(props);
    }

    render() {
        return (
            <div className='hero-unit'>
                <h1>AC Browser</h1>
                <QueryArea />
            </div>
        );
    }

    static renderItem(item, index) {
        return <li key={index}>{item}</li>;
    }
}

