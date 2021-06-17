import csv
import datetime
import io
import time
from typing import Iterator, Optional


def get_visibility_score(frequency, rank, page):
    """Calculate Visibility Score for the keyword."""
    visibility_score = 0
    # Our formula /1000 give negative value of 1m plus rank so limit the rank
    if frequency and frequency > 1000000:
        frequency = 999999
    else:
        frequency = 0
    keyword_quantity_score = round(((1000 - (frequency / 1000)) / 10), 1)
    if page == 1 and rank <= 3:
        search_share = 42
    elif page == 1 and rank >= 4 and rank <= 16:
        search_share = 38
    elif page == 2:
        search_share = 16
    elif page == 3:
        search_share = 4
    else:
        search_share = 0
    if search_share:
        visibility_score = round(
            (keyword_quantity_score * search_share) / 100, 2
        )
    return visibility_score


class StringIteratorIO(io.TextIOBase):
    def __init__(self, iter: Iterator[str]):
        self._iter = iter
        self._buff = ""

    def readable(self) -> bool:
        return True

    def _read1(self, n: Optional[int] = None) -> str:
        while not self._buff:
            try:
                self._buff = next(self._iter)
            except StopIteration:
                break
        ret = self._buff[:n]
        self._buff = self._buff[len(ret) :]
        return ret

    def read(self, n: Optional[int] = None) -> str:
        line = []
        if n is None or n < 0:
            while True:
                m = self._read1()
                if not m:
                    break
                line.append(m)
        else:
            while n > 0:
                m = self._read1(n)
                if not m:
                    break
                n -= len(m)
                line.append(m)
        return "".join(line)


def clean_global_keyword(csv_file):
    ct = str(datetime.datetime.now())
    csvfile1 = csv_file.read().decode("utf-8").splitlines()
    csvfile1.pop(0)
    reader = csv.DictReader(csvfile1, delimiter=",")
    order = [
        "Department",
        "Search Term",
        "Search Frequency Rank",
        "#1 Clicked ASIN",
        "#2 Clicked ASIN",
        "#3 Clicked ASIN",
    ]

    # define renamed columns via dictionary
    renamer = {
        "Department": "department",
        "Search Term": "name",
        "Search Frequency Rank": "frequency",
        "#1 Clicked ASIN": "asin_1",
        "#2 Clicked ASIN": "asin_2",
        "#3 Clicked ASIN": "asin_3",
    }

    # define column names after renaming
    new_cols = [renamer.get(x, x) for x in order]
    new_cols.append("create_date")

    tmp_path = "/tmp/global_keywords_data_" + str(time.time()) + ".csv"
    with open(tmp_path, "w", newline="") as csvfile_out:

        writer = csv.writer(csvfile_out, delimiter=",")

        writer.writerow(new_cols)
        data = []
        department = None
        order.append("create_date")
        for item in reader:
            r = item.copy()
            if department is None:
                department = r["Department"]

            if (
                not r["Search Term"]
                or r["Search Term"] == ""
                or len(r["Search Term"]) <= 0
            ):
                pass
            else:
                for key, value in r.items():
                    r[key] = value or ""
                    r[key] = r[key].replace(",", "")
                r["create_date"] = ct
                if r["Search Term"]:
                    data.append([r[k] for k in order])
        writer.writerows(data)
    return tmp_path, department
