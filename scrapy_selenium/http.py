"""This module contains the ``SeleniumChromeRequest`` class"""
import copy
from scrapy import Request


class SeleniumChromeRequest(Request):
    """Scrapy ``Request`` subclass providing additional arguments"""

    def __init__(self, url, callback=None, wait_time=None, wait_until=None, screenshot=False, selenium_action=None, fake_google_uule=True, apply_evasions=True, meta=None,
                 *args, **kwargs):
        """Initialize a new Selenium request

        Parameters
        ----------
        wait_time: int
            The number of seconds to wait.
        wait_until: method
            One of the "selenium.webdriver.support.expected_conditions". The response
            will be returned until the given condition is fulfilled.
        screenshot: bool
            If True, a screenshot of the page will be taken and the data of the screenshot
            will be returned in the response "meta" attribute.
        selenium_action: SeleniumActionClass
            Any class with a apply() function for custom selenium navigation on the page,
            will be called after visiting the url and before a screenshot is taken
        fake_google_uule: bool
            If true will fake google uule cookie
        """

        meta = copy.deepcopy(meta) or {}
        selenium_meta = meta.setdefault('selenium', {})

        if fake_google_uule:
            selenium_meta['fake_google_uule'] = True
        if screenshot:
            selenium_meta['screenshot'] = True
        if apply_evasions:
            selenium_meta['apply_evasions'] = True

        # FIXME: using all arguments in scrapy-splash style -> working also for classes?
        self.selenium_action = selenium_action

        super(SeleniumChromeRequest, self).__init__(url, callback, meta=meta, *args, **kwargs)

    def __str__(self):
        return super(SeleniumChromeRequest, self).__str__()

    __repr__ = __str__

    def apply_action(self, driver):
        if self.selenium_action:
            self.selenium_action.apply_action(driver=driver, request=self)
