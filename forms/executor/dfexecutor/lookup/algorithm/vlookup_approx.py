#  Copyright 2022-2023 The FormS Authors.
#
#  Licensed under the Apache License, Version 2.0 (the "License");
#  you may not use this file except in compliance with the License.
#  You may obtain a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
#  Unless required by applicable law or agreed to in writing, software
#  distributed under the License is distributed on an "AS IS" BASIS,
#  WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#  See the License for the specific language governing permissions and
#  limitations under the License.
import numpy as np
import pandas as pd

from forms.executor.dfexecutor.lookup.utils import approx_binary_search, set_dtype


# Uses approximate binary search.
def vlookup_approx(values, df, col_idxes) -> pd.DataFrame:
    df_arr: list = []
    for i in range(len(values)):
        value, col_idx = values[i], col_idxes[i]
        value_idx = approx_binary_search(value, list(df.iloc[:, 0]))
        result = np.nan
        if value_idx != -1:
            result = df.iloc[value_idx, col_idx - 1]
        df_arr.append(result)
    return pd.DataFrame(df_arr)


# Uses np.searchsorted as a fast binary search.
def vlookup_approx_np(values, df, col_idxes) -> pd.DataFrame:
    search_range = df.iloc[:, 0]
    value_idxes = np.searchsorted(search_range.to_numpy(), values.to_numpy(), side="left")
    result_arr = [np.nan] * len(values)
    for i in range(len(values)):
        value, value_idx, col_idx = values.iloc[i], value_idxes[i], col_idxes.iloc[i]
        if value_idx >= len(search_range) or value != search_range.iloc[value_idx]:
            value_idx -= 1
        if value_idx != -1:
            result_arr[i] = df.iloc[value_idx, col_idx - 1]
    return pd.DataFrame(result_arr)


# Attempt to use list comprehension for a performance increase.
def vlookup_approx_np_lc(values, df, col_idxes) -> pd.DataFrame:
    search_range = df.iloc[:, 0]
    value_idxes = np.searchsorted(search_range.to_numpy(), values.to_numpy(), side="left")
    value_idxes = [((value_idxes[i] - 1)
                    if (value_idxes[i] >= len(search_range) or values.iloc[i] != search_range.iloc[value_idxes[i]])
                    else value_idxes[i]) for i in range(len(value_idxes))]
    result_arr = [df.iloc[value_idxes[i], col_idxes.iloc[i] - 1] if value_idxes != -1 else np.nan
                  for i in range(len(values))]
    return pd.DataFrame(result_arr)


# Vectorizes the entire operation using numpy.
def vlookup_approx_np_vector(values, df, col_idxes) -> pd.DataFrame:
    search_range = df.iloc[:, 0]
    value_idxes = np.searchsorted(search_range.to_numpy(), values.to_numpy(), side="left")
    greater_than_length = np.greater_equal(value_idxes, len(search_range))
    value_idxes_no_oob = np.minimum(value_idxes, len(search_range) - 1)
    search_range_values = np.take(search_range, value_idxes_no_oob)
    approximate_matches = values.to_numpy() != search_range_values.to_numpy()
    combined = np.logical_or(greater_than_length, approximate_matches).astype(int)
    adjusted_idxes = value_idxes - combined
    row_res = np.take(df.to_numpy(), adjusted_idxes, axis=0)
    res = row_res[np.arange(len(col_idxes)), col_idxes.astype(int) - 1]
    nan_idxes = (adjusted_idxes == -1).nonzero()
    return set_dtype(res, nan_idxes)


def vlookup_approx_pd_merge(values, df, col_idxes) -> pd.DataFrame:
    sorted_values = values.sort_values()
    left = pd.DataFrame({"join_col": sorted_values.reset_index(drop=True)}).astype(np.float64)
    right = df.rename(columns={df.columns[0]: "join_col"})
    right["join_col"] = right["join_col"].astype(np.float64)
    merged = pd.merge_asof(left, right, on="join_col").to_numpy()
    res = pd.DataFrame(merged, index=sorted_values.index).sort_index().to_numpy()
    chosen = res[np.arange(len(col_idxes)), col_idxes.astype(int) - 1]
    return set_dtype(chosen)


def vlookup_approx_constants(value, df, col_idx, size) -> pd.DataFrame:
    if value < df.iloc[0, 0]:
        val = np.nan
    else:
        row_idx = np.searchsorted(df.iloc[:, 0].to_numpy(), value)
        if row_idx == size or df.iloc[row_idx, 0] != value:
            row_idx -= 1
        val = df.iloc[row_idx, int(col_idx - 1)]
    return pd.DataFrame(np.full(size, val))
