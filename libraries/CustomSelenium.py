import logging
import zipfile
from pathlib import Path
from RPA.core.webdriver import start
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options


class CustomSelenium(object):
    """
    Custom Selenium class to manage web scraping with different browsers.
    This should be used as a base class for other web scraping classes.

    Attributes
    ----------
    driver : WebDriver
        The Selenium WebDriver instance.
    logger : logging.Logger
        Logger instance for the class.
    custom_logger : logging.Logger
        Custom logger instance for specific logging.
    output_path : pathlib.Path
        Path to store output files.
    user_agent : str
        Custom user-agent string for the browser.
    """

    def __init__(self):
        """
        Initialize the CustomSelenium instance.
        """
        self.driver = None
        self.logger = logging.getLogger(__name__)
        self.custom_logger = logging.getLogger(f"{self}")
        self.output_path = Path(f"output/{self}")
        self.user_agent = (
            "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/60.0.3112.50 Safari/537.36"
        )

    def setup_crawler(self, browser: str = "Chrome"):
        """
        Set up the crawler with the specified browser.

        Parameters
        ----------
        browser : str, optional
            The browser to use for crawling, by default "Chrome".
        """
        self.output_path.mkdir(parents=True, exist_ok=True)
        self.set_webdriver(browser)
        self._setup_custom_logger()

    def set_webdriver(self, browser: str = "Chrome"):
        """
        Set the WebDriver for the specified browser.

        Parameters
        ----------
        browser : str, optional
            The browser to use for the WebDriver, by default "Chrome".

        Raises
        ------
        ValueError
            If the specified browser is not supported.
        """
        if browser.lower() == "chrome":
            options = self._set_chrome_options()
        elif browser.lower() == "firefox":
            options = self._set_firefox_options()
        else:
            raise ValueError(f"Browser '{browser}' is not supported")

        self.driver = start(browser, options=options)
        self.driver.implicitly_wait(20)
        self.driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")

    def set_page_size(self, width: int, height: int):
        """
        Set the browser window size.

        Parameters
        ----------
        width : int
            The desired width of the browser window.
        height : int
            The desired height of the browser window.
        """
        current_window_size = self.driver.get_window_size()

        html = self.driver.find_element(By.TAG_NAME, "html")
        inner_width = int(html.get_attribute("clientWidth"))
        inner_height = int(html.get_attribute("clientHeight"))

        target_width = width + (current_window_size["width"] - inner_width)
        target_height = height + (current_window_size["height"] - inner_height)
        self.driver.set_window_rect(width=target_width, height=target_height)

    def open_url(self, url: str, screenshot: str = None):
        """
        Open a URL in the browser and optionally take a screenshot.

        Parameters
        ----------
        url : str
            The URL to open.
        screenshot : str, optional
            The filename to save the screenshot, by default None.
        """
        self.driver.get(url)
        if screenshot:
            self.driver.get_screenshot_as_file(self.output_path / screenshot)

    def zip_output(self):
        """
        Zip the output files in the output directory.
        """
        with zipfile.ZipFile(Path("output") / f"output_{self}.zip", "w") as zf:
            for file in self.output_path.iterdir():
                if file.is_file():
                    zf.write(file, file.name)

        self.custom_logger.info("Output files zipped successfully.")

    def driver_quit(self):
        """
        Quit the WebDriver instance.
        """
        if self.driver:
            self.driver.quit()

    def _set_chrome_options(self) -> Options:
        """
        Set options for the Chrome browser.

        Returns
        -------
        Options
            The ChromeOptions instance with the configured settings.
        """
        options = webdriver.ChromeOptions()
        options.add_argument("--headless")
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-extensions")
        options.add_argument("--disable-web-security")
        options.add_argument("--start-maximized")
        options.add_argument("--disable-gpu")
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument("--ignore-certificate-errors")
        options.add_argument("--allow-running-insecure-content")
        options.add_argument(f"--user-agent={self.user_agent}")
        options.add_experimental_option("excludeSwitches", ["enable-automation"])
        options.add_experimental_option("excludeSwitches", ["enable-logging"])
        options.add_experimental_option("useAutomationExtension", False)
        return options

    def _set_firefox_options(self) -> Options:
        """
        Set options for the Firefox browser.

        Returns
        -------
        Options
            The FirefoxOptions instance with the configured settings.
        """
        options = webdriver.FirefoxOptions()
        options.add_argument("--headless")
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-extensions")
        options.add_argument("--disable-web-security")
        options.add_argument("--start-maximized")
        options.add_argument("--disable-gpu")
        options.add_argument("--ignore-certificate-errors")
        options.add_argument("--allow-running-insecure-content")
        options.add_argument(f"--user-agent={self.user_agent}")
        return options

    def _setup_custom_logger(self):
        """
        Set up the custom logger for the instance.
        """
        self.custom_logger.setLevel(logging.INFO)
        formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
        file_handler = logging.FileHandler(self.output_path / "custom.log")
        file_handler.setFormatter(formatter)
        self.custom_logger.addHandler(file_handler)

    def __str__(self):
        """
        Return the name of the class.

        Returns
        -------
        str
            The name of the class.
        """
        return self.__class__.__name__
