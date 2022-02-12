from objexplore.utils import is_empty
import pandas as pd


def test_dataframe():
    df = pd.DataFrame()
    assert is_empty(df)
