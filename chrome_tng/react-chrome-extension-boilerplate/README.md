# React Chrome Extension Boilerplate

[![Build Status](https://travis-ci.org/jhen0409/react-chrome-extension-boilerplate.svg)](https://travis-ci.org/jhen0409/react-chrome-extension-boilerplatee)
[![NPM version](http://img.shields.io/npm/v/react-chrome-extension-boilerplate.svg?style=flat)](https://www.npmjs.com/package/react-chrome-extension-boilerplate)

Boilerplate for Chrome extension React.js project.

## Included

 - [react](https://github.com/facebook/react)
 - [react-hot-loader](https://github.com/gaearon/react-hot-loader)
 - [redux (1.0.0rc)](https://github.com/gaearon/redux/tree/e39afbec270e9381df3d23dfa2f770c44f488380)
 - [react-redux](https://github.com/gaearon/react-redux)
 - [redux-devtools](https://github.com/gaearon/redux-devtools)
 - [webpack](https://github.com/webpack/webpack)
 - [babel](https://github.com/babel/babel)
 - [gulp-](https://github.com/gulpjs/gulp)
   - [jade](https://github.com/phated/gulp-jade)
   - [livereload](https://github.com/vohof/gulp-livereload)
   - [babel](https://github.com/babel/gulp-babel)
   - ...
 - [classnames](https://github.com/JedWatson/classnames)
 - [todomvc-app-css](https://github.com/tastejs/todomvc-app-css)
 - ...

## Example

The example is edited from [Redux](https://github.com/gaearon/redux) TodoMVC example.

#### Popup

![Popup](example-popup.gif)

The `todos` state will be saved to `chrome.storage.local`.

#### Window

![Popup](example-window.gif)

The context menu is created by content script(start script at visiting github.com).

If you want Packaged app, You can edit `manifest.{env}.json`.
```json
...
  "app": {
    "launch": {
      "local_path": "app.html",
      "container": "panel",
      "width": 800,
      "height": 500
    }
  },
...
```

and remove `browser_action`.

## Installation

```bash
# required node.js/io.js
# clone it
npm install

# or npm way
npm install react-chrome-extension-boilerplate --dev
```

## Development

```bash
# build files to './dev'
# watch files change
# start WebpackDevServer
npm run dev
```

You can load unpacked extensions with `./dev`.

#### React/Flux hot reload

This boilerplate uses Webpack and react-hot-loader, and use Redux. You can hot reload by editing related files of Popup & Window.

#### LiveReload

This boilerplate uses LiveReload except for Popup & Window. You can let chrome runtime reload by editing content & background scripts.

## Build

```bash
# build files to './build'
npm run build
```

## Build & Compress ZIP file

```bash
# compress build folder to archive.zip
npm run compress
```

## Test (Work in progress)

The test use [sinon-chrome](https://github.com/vitalets/sinon-chrome).

```
npm test
```

## LICENSE

[MIT](LICENSE)
