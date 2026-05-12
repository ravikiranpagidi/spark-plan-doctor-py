from __future__ import annotations


class FakeDataFrame:
    def __init__(self, plan_text):
        self.plan_text = plan_text
        self.write = FakeWriter(self)

    def explain(self, mode):
        print(self.plan_text)


class FakeWriter:
    def __init__(self, df):
        self.df = df
        self.format_name = None
        self.mode_name = None
        self.saved_table = None

    def format(self, name):
        self.format_name = name
        return self

    def mode(self, name):
        self.mode_name = name
        return self

    def saveAsTable(self, table):
        self.saved_table = table


class FakeConf:
    def __init__(self, values=None):
        self.values = values or {}

    def get(self, key):
        return self.values.get(key)


class FakeSpark:
    version = "3.5.0"

    def __init__(self, conf=None):
        self.conf = FakeConf(conf)
        self.created = []
        self.queries = []

    def createDataFrame(self, rows):
        df = FakeDataFrame("")
        df.rows = rows
        self.created.append(df)
        return df

    def sql(self, query):
        self.queries.append(query)
        return FakeDataFrame("== Physical Plan ==\nFileScan parquet t PartitionFilters: [], PushedFilters: []")
