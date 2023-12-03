import pandas as pd
from pandas.api.types import is_numeric_dtype

from taskweaver.plugin import Plugin, register_plugin


@register_plugin
class AnomalyDetectionPlugin(Plugin):
    def __call__(self, df: pd.DataFrame, time_col_name: str, value_col_name: str):

        """
        anomaly_detection function identifies anomalies from an input dataframe of time series.
        It will add a new column "Is_Anomaly", where each entry will be marked with "True" if the value is an anomaly
        or "False" otherwise.

        :param df: the input data, must be a dataframe
        :param time_col_name: name of the column that contains the datetime
        :param value_col_name: name of the column that contains the numeric values.
        :return df: a new df that adds an additional "Is_Anomaly" column based on the input df.
        :return description: the description about the anomaly detection results.
        """
        try:
            df[time_col_name] = pd.to_datetime(df[time_col_name])
        except Exception:
            print("Time column is not datetime")
            return

        if not is_numeric_dtype(df[value_col_name]):
            try:
                df[value_col_name] = df[value_col_name].astype(float)
            except ValueError:
                print("Value column is not numeric")
                return

        mean, std = df[value_col_name].mean(), df[value_col_name].std()
        cutoff = std * 3
        lower, upper = mean - cutoff, mean + cutoff
        df["Is_Anomaly"] = df[value_col_name].apply(lambda x: x < lower or x > upper)
        anomaly_count = df["Is_Anomaly"].sum()
        description = "There are {} anomalies in the time series data".format(anomaly_count)

        self.ctx.add_artifact(
            name="anomaly_detection_results",
            file_name="anomaly_detection_results.csv",
            type="df",
            val=df,
        )

        return df, description
