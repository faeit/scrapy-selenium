Object.defineProperty(HTMLIFrameElement.prototype, 'contentWindow', {
    get: function () {
        return window;
    }
});