from robocorp.tasks import task
from robocorp import workitems
from libraries.AlJazeeraCrawler import AlJazeeraCrawler


@task
def task():
    crawler = AlJazeeraCrawler()
    crawler.setup_home_page()

    for item in workitems.inputs:
        search_term = item.payload.get("search_term", "Olympics")
        number_of_months = item.payload.get("number_of_months", 1)

        crawler.search_news(search_term, number_of_months=number_of_months)
        crawler.zip_output()

    crawler.driver_quit()
