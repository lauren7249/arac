var ExtractTextPlugin = require('extract-text-webpack-plugin');
var path = require('path');
var root = path.join(__dirname, '..');
var context = path.join(root, 'src');
var clientDir = path.join(context, 'client');

var modules = ['ui', 'mixins'];
var moduleDirectories = modules.map(function(mod) {
    return path.join(clientDir, mod);
});

module.exports = {
    entry: {
        background: path.join(context, 'background.js'),
        client: path.join(context, 'client.jsx')
    },

    context: context,

    output: {
        path: path.join(root, 'build/js'),
        filename: '[name]-bundle.js'
    },

    module: {
        loaders: [{
            test: /\.jsx?$/,
            loader: 'babel',
            exclude: [path.join(root, 'node_modules'), path.join(context, 'node_modules')]
        },
            {
                test: /\.jpe?g$|\.gif$|\.png$|\.svg$|\.woff$|\.ttf$/,
                loader: 'file'
            },
            {
                test: /\.css$/,
                loader: ExtractTextPlugin.extract('style-loader', 'css-loader')
            }]
    },

    plugins: [
        new ExtractTextPlugin('../css/[name]-bundle.css')
    ],

    resolve: {
        extensions: ['', '.js', '.jsx'],
        moduleDirectories: moduleDirectories,
        root: moduleDirectories

    },

    resolveLoader: {
        moduleDirectories: [
            moduleDirectories
        ]
    }
};
