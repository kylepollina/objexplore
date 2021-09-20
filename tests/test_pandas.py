
from objexplore.utils import is_selectable
import pandas as pd


def test_dataframe():
    df = pd.DataFrame()
    assert is_selectable(df)
