import logging
import pandas as pd
import re
import urllib
from pandas.tseries.offsets import DateOffset
from datetime import datetime
from time import sleep
from pathlib import Path
from selenium.webdriver.common.by import By
from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver.remote.webelement import WebElement

from libraries.CustomSelenium import CustomSelenium


class AlJazeeraCrawler(CustomSelenium):
    """
    Al Jazeera news crawler that extends the CustomSelenium class.

    Attributes
    ----------
    logger : logging.Logger
        Logger instance for the class.
    output_path : pathlib.Path
        Path to store output files.
    """

    def __init__(self):
        """
        Initialize the AlJazeeraCrawler instance.
        """
        super().__init__()
        self.logger = logging.getLogger(__name__)
        self.output_path = Path(f"output/{self}")

    def setup_home_page(self, browser: str = "Chrome", url: str = "https://www.aljazeera.com/", screenshot: str = None):
        """
        Set up the home page for crawling.

        Parameters
        ----------
        browser : str, optional
            The browser to use for crawling, by default "Chrome".
        url : str, optional
            The URL to open, by default "https://www.aljazeera.com/".
        screenshot : str, optional
            The filename to save the screenshot, by default None.
        """
        self.setup_crawler(browser)
        self.open_url(url, screenshot)
        self.set_page_size(1920, 1080)
        self.custom_logger.info("Al Jazeera News page opened successfully.")

    def search_news(self, search_term: str, *, number_of_months: int = 1):
        """
        Search for news articles based on a search term and time period.

        Parameters
        ----------
        search_term : str
            The term to search for in news articles.
        number_of_months : int, optional
            The number of past months to include in the search, by default 1.
        """
        self.custom_logger.info(f"Searching news for term {search_term} for the last {number_of_months} month(s).")
        self._search_by_term(search_term)
        self._sort_results()
        self._save_news_to_excel(search_term, number_of_months)

    def _find_element_by_xpath(self, xpath: str, *, parent: WebElement = None, multiple: bool = False) -> WebElement:
        """
        Find an element or elements by XPath.

        Parameters
        ----------
        xpath : str
            The XPath string to locate the element.
        parent : WebElement, optional
            The parent element to search within, by default None.
        multiple : bool, optional
            Whether to find multiple elements, by default False.

        Returns
        -------
        WebElement or None
            The located WebElement or None if not found.
        """
        if not parent:
            parent = self.driver

        try:
            if multiple:
                elements = parent.find_elements(By.XPATH, xpath)
                return elements
            else:
                element = parent.find_element(By.XPATH, xpath)
                return element
        except NoSuchElementException:
            self.custom_logger.error(f"Element not found: {xpath}")
            return None

    def _search_by_term(self, search_term: str):
        """
        Perform the search operation on the Al Jazeera website.

        Parameters
        ----------
        search_term : str
            The term to search for.
        """
        search_button = self._find_element_by_xpath('//div[@class="site-header__search-trigger"]')
        search_button.click()

        search_input = self._find_element_by_xpath('//input[@class="search-bar__input" and @type="text"]')
        search_input.send_keys(search_term)

        search_button = self._find_element_by_xpath('//div[@class="search-bar__button"]')
        search_button.click()

    def _sort_results(self, sort_by: str = "Date"):
        """
        Sort the search results.

        Parameters
        ----------
        sort_by : str, optional
            The criteria to sort by, by default "Date".
        """
        sort_by_container = self.driver.find_element(By.ID, "search-sort-option")
        sort_by_container.click()

        sort_by_element = self._find_element_by_xpath(
            f".//option[@value='{sort_by.lower()}']", parent=sort_by_container
        )
        sort_by_element.click()

    def _scrape_news_item(self, news_item: WebElement, search_term: str) -> dict[str, any]:
        """
        Scrape the details of a single news item.

        Parameters
        ----------
        news_item : WebElement
            The news item element to scrape.
        search_term : str
            The search term to count occurrences of.

        Returns
        -------
        dict or None
            A dictionary with the news item details, or None if not a valid news article.
        """
        title_xpath = './/a[not(contains(@href, "tag")) and @class="u-clickable-card__link"]'
        title_element = self._find_element_by_xpath(title_xpath, parent=news_item)
        title = title_element.text if title_element else None

        if not title:
            return None

        date_element = self._find_element_by_xpath(
            ".//div[contains(@class, 'date-simple')]/span[@aria-hidden='true']", parent=news_item
        )
        date = (
            datetime.strptime(date_element.text.removeprefix("Last update ").strip(), "%d %b %Y")
            if date_element
            else None
        )

        description_element = self._find_element_by_xpath(".//div[@class='gc__excerpt']/p", parent=news_item)
        description = description_element.text if description_element else None

        picture_element = self._find_element_by_xpath(".//img", parent=news_item)
        if picture_element:
            title_hash = hash(title) if title else 0
            picture_filepath = self.output_path / f"{title_hash}.png"
            src = picture_element.get_attribute("src")
            if src:
                urllib.request.urlretrieve(src, picture_filepath)
        picture_filename = picture_filepath.name if picture_element else None

        search_phrase_count = title.lower().count(search_term.lower()) if title else 0
        search_phrase_count += description.lower().count(search_term.lower()) if description else 0

        has_money = False
        money_pattern = re.compile(r"(\$[\d,]+(\.\d+)?|\d+ dollars|\d+ USD)")
        money_matches = money_pattern.findall(title) or money_pattern.findall(description)
        if money_matches:
            has_money = True

        return {
            "title": title,
            "date": date,
            "description": description,
            "picture_filename": picture_filename,
            "search_phrase_count": search_phrase_count,
            "has_money": has_money,
        }

    def _save_news_to_excel(self, search_term: str, number_of_months: int):
        """
        Save the scraped news items to an Excel file.

        Parameters
        ----------
        search_term : str
            The search term used to find news articles.
        number_of_months : int
            The number of past months to include in the search.
        """
        min_date = datetime.today()
        if number_of_months > 0:
            min_date -= DateOffset(months=number_of_months - 1)
        min_date = min_date.replace(day=1)

        news_df = pd.DataFrame(
            columns=["title", "date", "description", "picture_filename", "search_phrase_count", "has_money"]
        )

        curr_item = 0
        article_container = self.driver.find_element(By.CLASS_NAME, "search-result__list")
        news_items = self._find_element_by_xpath(".//article", parent=article_container, multiple=True)
        while news_items:
            news_item = news_items.pop(0)
            self.driver.execute_script("arguments[0].scrollIntoView();", news_item)

            new_row = self._scrape_news_item(news_item, search_term)
            if new_row:
                if new_row["date"] and new_row["date"].date() < min_date.date():
                    self.custom_logger.info("Reached the minimum date.")
                    break

                news_df = pd.concat([news_df, pd.DataFrame(new_row, index=[0])])

            curr_item += 1

            if not news_items:
                show_more_button = self._find_element_by_xpath(
                    './/button[contains(@class, "show-more-button")]/span[@aria-hidden="true"]',
                    parent=article_container,
                )
                if show_more_button:
                    self.driver.execute_script("arguments[0].scrollIntoView();", show_more_button)
                    show_more_button.click()
                    self.custom_logger.info("Loading more news items...")
                    sleep(5)
                    news_items = self._find_element_by_xpath(".//article", parent=article_container, multiple=True)
                    news_items = news_items[curr_item:]

        news_df.to_excel(self.output_path / "news.xlsx", index=False)
        self.custom_logger.info("News saved to Excel successfully.")
