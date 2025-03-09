import requests
import xmltodict
from pprint import pprint
from typing import Dict, List
from celery import Celery, Task
from bs4 import BeautifulSoup


from pydantic import (
    BaseModel,
    computed_field,
)

PAGES = [1, 2]
MAIN_URL = (
    "https://zakupki.gov.ru/epz/order/extendedsearch/results.html?fz44=on&pageNumber="
)

app = Celery("run")

default_config = "celeryconfig"
app.config_from_object(default_config)


class XmlForm(BaseModel):
    url: str

    @computed_field
    @property
    def full_url(cls) -> str:
        return "https://zakupki.gov.ru" + cls.url.replace("view.html", "viewXml.html")


class ParsingTask(Task):
    def run(self, *args, page_number: int, **kwargs) -> List[XmlForm]:
        page = self.get_page(page_number)
        return self.collect_urls(page)

    def get_page(self, page_number: int) -> requests.Response:
        """Get html page to be parsed."""
        response = requests.get(f"{MAIN_URL}{page_number}")
        response.raise_for_status()
        return response

    def collect_urls(self, page: requests.Response) -> List[XmlForm]:
        """Select html forms to be parsed.

        Modify paths to get xml forms to be parsed.
        """
        soup = BeautifulSoup(page.content, "html5lib")
        forms = [
            item.get("href")
            for item in soup.find_all("a")
            if "printForm/view" in item.get("href", [])
        ]
        return [XmlForm(url=form) for form in forms]


@app.task(bind=True, base=ParsingTask)
def get_xml_forms(self, page_number: int) -> List[XmlForm]:
    try:
        return ParsingTask().run(page_number=page_number)
    except requests.exceptions.HTTPError as exc:
        raise self.retry(countdown=6, exc=exc, max_retries=40)


@app.task(bind=True)
def parse(self, form: XmlForm) -> requests.Response | None:
    try:
        response = requests.get(form.full_url)
        response.raise_for_status()
        return response
    except requests.exceptions.HTTPError:
        return None


def main() -> Dict[str, str | None]:
    """Show form name and its creation date."""
    form_and_date = {}
    for page in PAGES:
        xmlforms = get_xml_forms.delay(page_number=page).get()
        for form in xmlforms:
            requested_xml_form = parse.apply_async(
                kwargs={"form": form},
            ).get()
            if requested_xml_form is None:
                form_and_date[form.full_url] = None
            else:
                xml_form_dict = xmltodict.parse(requested_xml_form.text)
                first_key = list(xml_form_dict.keys())[0]
                date_published = xml_form_dict[first_key]["commonInfo"].get(
                    "publishDTInEIS"
                )
                form_and_date[form.full_url] = date_published
    return pprint(form_and_date)


if __name__ == "__main__":
    main()
