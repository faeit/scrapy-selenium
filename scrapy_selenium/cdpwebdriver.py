from selenium.webdriver import Chrome as _Chrome
# from seleniumwire.webdriver.browsers import Chrome as _Chrome

import time, base64, math, logging


class Chrome(_Chrome):
    """Extends the Chrome webdriver to provide additional methods for advanced devtools communication."""

    def __init__(self, *args, **kwargs):
        """Initialise a new Chrome WebDriver instance.
        """
        super().__init__(*args, **kwargs)

    def quit(self):
        super().quit()

    def add_script(self, driver, script):
        self.execute_cdp_cmd("Page.addScriptToEvaluateOnNewDocument", {"source": script})

    def remove_history(self, driver):
        """

        :param driver:
        :return:
        """
        #driver.execute_cdp_cmd("Network.getAllCookies", {})
        driver.execute_cdp_cmd("Network.clearBrowserCache", {})
        driver.execute_cdp_cmd("Network.clearBrowserCookies", {})
        #driver.execute_cdp_cmd("Network.getAllCookies", {})

    def disable_browserchache(self, driver):
        """

        :param driver:
        :return:
        """
        driver.execute_cdp_cmd("Network.setCacheDisabled", {"cacheDisabled": True})

    def capture_screenshot(self, driver, path):
        """
        Note: Heavily oriented on pyppeteer

        :param driver:
        :param path:
        :return:
        FIXME: revert Metrics override, screen scaling, orientation, omitBackground
        """
        metrics = driver.execute_cdp_cmd("Page.getLayoutMetrics",{})

        width = math.ceil(metrics['contentSize']['width'])
        height = math.ceil(metrics['contentSize']['height'])

        driver.execute_cdp_cmd("Emulation.setDeviceMetricsOverride",
         {'mobile': False,
         'width': width,
         'height': height,
         'deviceScaleFactor': 1,
         'screenOrientation': dict(angle=0, type='portraitPrimary'),
         })
        result = driver.execute_cdp_cmd("Page.captureScreenshot", {"format": "png"})
        buffer = base64.b64decode(result.get('data', b''))
        if path:
            with open(path, 'wb') as f:
                f.write(buffer)

    def override_location(self, driver, location):
        """

        :param driver:
        :param location:
        :return:
        """
        result = driver.execute_cdp_cmd("Emulation.setGeolocationOverride", location)

    def override_location_google_uule_cookie(driver, location, google_domains = ["www.google.de"]):
        """

        :param driver:
        :param location: Expects a dict with ("accuracy", "latitude", "longitude")
        :return:
        """
        # TODO: make it configurable

        # build googles uule location cookie
        radius = int(round(location['accuracy'] * 1000))
        latitude_e7 = int(round(location['latitude'] * 10000000))
        longitude_e7 = int(round(location['longitude'] * 10000000))
        time_in_milliseconds = int(round(time.time() * 1000)) * 1000
        uule_str = """role:%d
producer:%d
provenance:%d
timestamp:%d
latlng{
latitude_e7:%d
longitude_e7:%d
}
radius:%d""" % (1, 12, 6, time_in_milliseconds, latitude_e7, longitude_e7, radius)
        google_location_string = "a+" + str(base64.b64encode(uule_str.encode("utf-8")), "utf-8")
        for google_domain in google_domains:
            driver.execute_cdp_cmd("Network.setCookie", {'name': 'UULE', 'value': google_location_string, 'domain': google_domain})