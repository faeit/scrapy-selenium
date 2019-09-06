from twisted.internet import reactor, defer
# from urllib.parse import urlunparse, urlparse, urlencode, urlsplit, parse_qsl


def deferredsleep(seconds):
    """

    :param seconds:
    :return:
    """
    d = defer.Deferred()
    reactor.callLater(0.1, d.callback, seconds)
    return d


# FIXME: helper functions for advanced rewriting in seleniumwire, TODO: extend RequestModifier class
'''
def  _rewrite_url(rm, request): # RequestModifier
    with rm._lock:
        rewrite_rules = rm._rewrite_rules[:]

    original_netloc = urlsplit(request.path).netloc

    # Rewrite parameters:
    parsed_url = urlparse(request.path)

    if parsed_url.netloc == "www.google.de" and parsed_url.path == "/search":
        new_args = {'num': 100}
        new_args.update(parse_qsl(parsed_url.query))
        intercepted_url = urlunparse((parsed_url.scheme, parsed_url.netloc, parsed_url.path, None, urlencode(new_args), None))
        request.path = intercepted_url

    for pattern, replacement in rewrite_rules:
        modified, count = pattern.subn(replacement, request.path)

        if count > 0:
            request.path = modified
            break

    modified_netloc = urlsplit(request.path).netloc

    if original_netloc != modified_netloc:
        # Modify the Host header if it exists
        if 'Host' in request.headers:
            request.headers['Host'] = modified_netloc
'''
