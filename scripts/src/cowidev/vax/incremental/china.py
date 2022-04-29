import time
import re
import random

import pandas as pd
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait as Wait

from cowidev.utils.clean import clean_count, extract_clean_date, clean_date
from cowidev.utils.web.scraping import get_driver, sel_options
from cowidev.vax.utils.base import CountryVaxBase


class China(CountryVaxBase):
    location: str = "China"
    source_url: str = "http://www.nhc.gov.cn/xcs/yqjzqk/list_gzbd.shtml"
    source_url_complete: str = "http://www.nhc.gov.cn/xcs/s2906/new_list.shtml"
    regex: dict = {
        "date": r"截至(20\d{2})年(\d{1,2})月(\d{1,2})日",
        "total_vaccinations": r"([\d\.]+\s*万)剂次",
    }
    regex_complete = {
        "title": r"国务院联防联控机制(20\d{2})年(\d{1,2})月(\d{1,2})日新闻发布会文字实录",
        "summary": r"截至(\d{1,2})月(\d{1,2})日.*疫苗([\d\.亿零]+万)剂次.*全程接种的?人数(?:为|.{0,9}达到)([\d\.亿零]+万)人",
        "vaccinated": r"(?:接种|疫苗)的?总人数(?:达到?|为)([\d\.亿零]+万)",
        "boosters": r"加强免疫(?:已经)?接种的?是?([\d\.亿零]+万)人",
    }
    num_links_complete = 3
    timeout = 30

    def read(self, last_update: str):
        data = []
        options = sel_options(headless=True, firefox=True)
        options.set_capability("pageLoadStrategy", "none")
        with get_driver(options=options, firefox=True, timeout=self.timeout) as driver:
            driver.get(self.source_url)
            time.sleep(random.randint(1, 2))
            Wait(driver, self.timeout).until(EC.presence_of_element_located((By.CLASS_NAME, "zxxx_list")))
            driver.execute_script("window.stop();")
            links = self._get_links(driver)
            for link in links:
                data_ = self._parse_data(driver, link)
                if data_["date"] <= last_update:
                    break
                data.append(data_)
            assert data_["date"] <= last_update, "Only read data back to: " + data_["date"]
        return pd.DataFrame(data)

    def _parse_data(self, driver, url):
        driver.get(url)
        time.sleep(random.randint(1, 2))
        Wait(driver, self.timeout).until(EC.text_to_be_present_in_element((By.ID, "xw_box"), "万剂次"))
        driver.execute_script("window.stop();")
        elem = driver.find_element_by_id("xw_box")
        return {
            "date": extract_clean_date(elem.text, self.regex["date"], "%Y %m %d"),
            "total_vaccinations": clean_count(re.search(self.regex["total_vaccinations"], elem.text).group(1)),
            "source_url": url,
        }

    def _get_links(self, driver) -> list:
        elems = driver.find_elements_by_css_selector("li>a")
        return [elem.get_property("href") for elem in elems]

    def read_complete(self):
        records = []
        options = sel_options(headless=True, firefox=True)
        options.set_capability("pageLoadStrategy", "none")
        with get_driver(options=options, firefox=True, timeout=self.timeout) as driver:
            driver.get(self.source_url_complete)
            time.sleep(random.randint(1, 2))
            Wait(driver, self.timeout).until(EC.presence_of_element_located((By.CLASS_NAME, "zxxx_list")))
            driver.execute_script("window.stop();")
            links = self._get_links_complete(driver)
            for link in links[: self.num_links_complete]:
                try:
                    record = self._parse_data_complete(driver, link)
                except:
                    print("Failed to parse:", link)
                    continue
                if record:
                    records.append(record)
        return pd.DataFrame(records)

    def _get_links_complete(self, driver):
        elems = driver.find_elements_by_css_selector("li>a")
        return [elem.get_property("href") for elem in elems if re.search(self.regex_complete["title"], elem.text)]

    def _parse_data_complete(self, driver, url):
        def _clean_count(num_as_str):
            num = float(re.search(r"([\d\.]+)万", num_as_str).group(1)) * 1e4
            num_100m = re.search(r"([\d\.]+)亿零?", num_as_str)
            if num_100m:
                num += float(num_100m.group(1)) * 1e8
            return int(num)

        driver.get(url)
        time.sleep(random.randint(1, 2))
        Wait(driver, self.timeout).until(EC.text_to_be_present_in_element((By.ID, "xw_box"), "到此结束"))
        driver.execute_script("window.stop();")
        elem = driver.find_element_by_id("xw_box")
        # Apply regex
        year = re.search(self.regex_complete["title"], driver.title).group(1)
        summary = re.search(self.regex_complete["summary"], elem.text)
        if summary:
            month, day, total_vaccinations, people_fully_vaccinated = summary.groups()
        else:
            return
        vaccinated = re.search(self.regex_complete["vaccinated"], elem.text)
        boosters = re.search(self.regex_complete["boosters"], elem.text)
        # Get metrics
        metrics = {
            "total_vaccinations": _clean_count(total_vaccinations),
            "people_vaccinated": _clean_count(vaccinated.group(1)) if vaccinated else None,
            "people_fully_vaccinated": _clean_count(people_fully_vaccinated),
            "total_boosters": _clean_count(boosters.group(1)) if boosters else None,
            "date": clean_date(f"{year}-{month}-{day}", "%Y-%m-%d"),
            "source_url": url,
        }
        return metrics

    def pipe_metadata(self, df: pd.DataFrame) -> pd.DataFrame:
        return df.assign(
            location=self.location,
        )

    def pipe_vaccine(self, df: pd.DataFrame) -> pd.DataFrame:
        return df.assign(vaccine="CanSino, IMBCAMS, KCONVAC, Sinopharm/Beijing, Sinopharm/Wuhan, Sinovac, ZF2001")

    def pipeline(self, df: pd.DataFrame) -> pd.DataFrame:
        return df.pipe(self.pipe_metadata).pipe(self.pipe_vaccine)

    def export(self):
        last_update = self.load_datafile().date.max()
        df = self.read(last_update)
        df_complete = self.read_complete()
        # Transform
        if not df.empty:
            df = df.pipe(self.pipeline)
        if not df_complete.empty:
            df_complete = df_complete.pipe(self.pipeline)
        # Merge
        if df.empty:
            df = df_complete
        elif not df_complete.empty:
            msk = ~df.date.isin(df_complete.date)
            df = pd.concat([df_complete, df.loc[msk]])
        # Export
        if not df.empty:
            self.export_datafile(df, attach=True)


def main():
    China().export()
