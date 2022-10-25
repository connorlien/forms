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
import pandas as pd

from forms.executor.executionnode import (
    RefExecutionNode,
    ExecutionNode,
)
from forms.executor.dfexecutor.utils import get_single_value


# Performs binary search for value VALUE in array ARR. Assumes the array is sorted.
# If the value is found, returns the index of the value.
# If the value is not found, returns the index of the value before the sorted value.
# If the value is less than the first value, return -1.
def approx_binary_search(value: any, arr: list) -> int:
    assert len(arr) > 0
    if value < arr[0]:
        return -1
    low, high = 0, len(arr) - 1
    while low <= high:
        mid = (high + low) // 2
        if arr[mid] < value:
            low = mid + 1
        elif arr[mid] > value:
            high = mid - 1
        else:
            return mid
    return (high + low) // 2


# Gets a literal value from a child and puts it in a dataframe with SIZE rows.
def get_literal_value(child: ExecutionNode, size: int) -> pd.DataFrame:
    value = get_single_value(child)
    result = value
    if not isinstance(value, pd.DataFrame):
        result = pd.DataFrame([value] * size)
    elif value.shape[0] == 1:
        result = pd.DataFrame([value.iloc[0, 0]] * size)
    return result


# Obtains the full dataframe for this lookup.
def get_df(child: RefExecutionNode) -> pd.DataFrame:
    ref = child.ref
    df: pd.DataFrame = child.table.get_table_content()
    return df.iloc[ref.row : ref.last_row + 1, ref.col : ref.last_col + 1]


# Clean string values by removing quotations.
def clean_string_values(values: pd.DataFrame):
    return values.applymap(lambda x: x.strip('"').strip("'") if isinstance(x, str) else x)


# Clean column indices by casting floats to integers.
def clean_col_idxes(col_idxes: pd.DataFrame):
    return col_idxes.applymap(lambda x: int(x))