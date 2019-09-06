try {
//    const getParameter = WebGLRenderingContext.getParameter FIXME: not needed?
    WebGLRenderingContext.prototype.getParameter = function (parameter) {

        if (parameter === 37445) {
            return 'Intel Inc.'
        }

        if (parameter === 37446) {
            return 'Intel Iris OpenGL Engine'
        }
        return getParameter(parameter)
    }
} catch (err) {}