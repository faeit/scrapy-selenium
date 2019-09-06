# -*- coding: utf-8 -*-
from selenium.webdriver.chrome.options import Options
# from seleniumwire.proxy.modifier import RequestModifier

import os, random, logging

from scrapy import signals
from scrapy.http import HtmlResponse

from twisted.internet import reactor, defer, task
from twisted.internet.defer import inlineCallbacks

from .evasions import EvasionMeasureFactory
from .cdpwebdriver import Chrome
from .helpers import deferredsleep


class SeleniumChromeDownloaderMiddleware(object):

    @classmethod
    def from_crawler(cls, crawler):
        """
        This method is used by Scrapy to create your spiders. Crawler settings will be forwarded to the spider middleware.
        :param crawler:
        :return: The instantiated spider middleware
        """
        middleware = cls(crawler.settings)
        crawler.signals.connect(middleware.spider_opened, signal=signals.spider_opened)
        crawler.signals.connect(middleware.spider_closed, signal=signals.spider_closed)
        return middleware

    def __init__(self, settings):
        """

        :param settings:
                apply_evasions: bool
            If True, various evasions in evasions/*.js are applied before page is visited
        """
        self.amount_drivers = int(settings.get('SELENIUM_MAX_BROWSERS_AVAILABLE'))
        self.browser_slots = defer.DeferredSemaphore(self.amount_drivers)
        self.concurrent_slots = defer.DeferredSemaphore(settings.get('CONCURRENT_REQUESTS'))
        self.delay = settings.get('DOWNLOAD_DELAY')
        self.randomize_delay = settings.get('RANDOMIZE_DOWNLOAD_DELAY')
        self.drivers = []
        self.screenshot_id = 0
        self.location = settings.get('SELENIUM_CHROME_GEOLOCATION')
        self.apply_evasions = settings.get('SELENIUM_CHROME_APPLY_EVASIONS')

        # FIXME: consider using chromedev tools request interception as an alternative to seleniumwire (maybe reference to pyppetteer or selenium java branch)
        # override seleniumwire request interception function with custom one
        # RequestModifier._rewrite_url = _rewrite_url

        chrome_options = Options()
        chrome_options.binary_location = settings.get('SELENIUM_CHROME_BINARY')
        # custom profile settings, FIXME: should be configurable via spider
        prefs = {
            "profile.managed_default_content_settings.geolocation": 1,
        }
        chrome_options.add_experimental_option("prefs", prefs)

        # FIXME: if needed customize user profile?
        # userProfile = "C:/a/b/profile"
        # chrome_options.add_argument('user-data-dir=' + userProfile)

        headless = settings.get('SELENIUM_CHROME_HEADLESS')

        if headless:
            chrome_options.add_argument("--headless")

        # FIXME: workaround for correct header in headless mode (refer to ... and ... )
        chrome_options.add_argument("--lang=de-DE,de;q=0.9,en-US;q=0.8,en;q=0.7")

        for parameter in settings.get('SELENIUM_CHROME_PARAMETERS'):
            chrome_options.add_argument(parameter)

        # start browsers
        for i in range(self.amount_drivers):
            driver = Chrome(
            executable_path=settings.get('SELENIUM_CHROMEDRIVER_BINARY'),
            chrome_options=chrome_options,
            service_args=["--verbose", "--log-path=C:/chrome/qc%d.log" % (i)] # FIXME: should be configurable via spider
            )
            self.drivers.append(driver)

            # apply javascript evasion measures
            if self.apply_evasions:
                for evasion in EvasionMeasureFactory.from_directory():
                    driver.add_script(evasion.javascript)

            # adapt geolocation to provided one
            driver.override_location(self.location)

    def __del__(self):
        """
        Destructor
        :return:
        """
        for driver in self.drivers:
            driver.close()

    @inlineCallbacks
    def process_request(self, request, spider):
        """

        :param request:
        :param spider:
        :return:
        Must either:
         - return None: continue processing this request
         - or return a Response object
         - or return a Request object
         - or raise IgnoreRequest: process_exception() methods of
           installed downloader middleware will be called
        FIXME/TODO: allow eager page visits
        """

        if 'selenium' not in request.meta:
            return

        # aquire concurrent-access-lock
        spider.logger.debug('process_request: aquire concurrent-access-lock for request %s' % request)
        yield self.concurrent_slots.acquire()
        spider.logger.debug('process_request: concurrent-access-lock for request %s aquired' % request)

        # aquire browser-slot-lock and associated driver
        spider.logger.debug('process_request: browser-slot-lock for request %s aquired' % request)
        yield self.browser_slots.acquire()
        spider.logger.debug('process_request: browser-slot-lock for request %s aquired' % request)
        # retrieve a free driver from queue FIXME: is this really thread-safe?
        driver = self.drivers.pop(0)

        selenium_options = request.meta['selenium']
        # TODO: set google specific fix/cookie only on google pages FIXME: generalize such page-specific preparations
        if selenium_options.get('fake_google_uule'):
            driver.override_location_google_uule_cookie(self.location)

        # call the website
        driver.get(request.url)

        # apply provided interaction step
        if request.selenium_action:
            request.selenium_action.apply_action(driver, request)

        # make a screenshot if required
        if not selenium_options.get('screenshot'):
            screenshot_filename = 'shot%d.png' % (self.screenshot_id)
            screenshot_path = os.path.join(os.getcwd(), 'screenshots', screenshot_filename)
            selenium_options['screenshot_id'] = screenshot_filename
            driver.capture_screenshot(screenshot_path)
            self.screenshot_id += 1
            spider.logger.info('Screenshot saved at: %s' % screenshot_path)

        # return html result for request with provided interaction
        new_body = driver.page_source
        # FIXME: Return custom response object
        new_response = HtmlResponse(url=request.url,
                                    status=200,
                                    body=new_body,
                                    request=request,
                                    encoding='utf-8',
                                    headers={'Content-Type': 'text/html; charset=utf-8'})

        driver.remove_history()  # remove temporary stuff FIXME: may add some measures

        # delay operation FIXME: maybe use scrapys delay logic by overriding downloader
        yield task.deferLater(reactor, self.download_delay(), deferredsleep, 1)

        self.drivers.append(driver)
        # release driver and associated browser-access-lock
        spider.logger.info('release lock: %s' % spider.name)
        self.browser_slots.release()
        spider.logger.info('lock released: %s' % spider.name)
        # release concurrent-access-lock

        return new_response

    def process_exception(self, request, exception, spider):
        """
        Called when a download handler or a process_request()
        (from other downloader middleware) raises an exception.
        :param request:
        :param exception:
        :param spider:
        :return: Must either:
         - return None: continue processing this exception
         - return a Response object: stops process_exception() chain
         - return a Request object: stops process_exception() chain
        """
        pass

    def spider_opened(self, spider):
        """

        :param spider:
        :return:
        """
        spider.logger.info('Spider opened: %s' % spider.name)

    def spider_closed(self, spider):
        """

        :param spider:
        :return:
        """
        spider.logger.info('Spider closed: %s' % spider.name)

    def download_delay(self):
        """

        :return:
        """
        if self.randomize_delay:
            return random.uniform(0.5 * self.delay, 1.5 * self.delay)
        return self.delay


