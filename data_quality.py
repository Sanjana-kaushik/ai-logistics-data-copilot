import pandas as pd

from database import run_query


def get_data_quality_results():
    shipments = run_query(
        """
        SELECT *
        FROM shipments
        """
    )

    results = []

    null_carriers = shipments["carrier"].isna().sum()

    missing_delivery_dates = (
        shipments["actual_delivery_date"]
        .isna()
        .sum()
    )

    invalid_delay_values = (
        pd.to_numeric(
            shipments["delay_days"],
            errors="coerce",
        )
        < 0
    ).sum()

    duplicate_shipment_ids = (
        shipments["shipment_id"]
        .duplicated()
        .sum()
    )

    results.append(
        {
            "rule_name": "Carrier must not be null",
            "failed_records": int(null_carriers),
            "status": (
                "Failed"
                if null_carriers > 0
                else "Passed"
            ),
        }
    )

    results.append(
        {
            "rule_name": (
                "Actual delivery date must not be null"
            ),
            "failed_records": int(
                missing_delivery_dates
            ),
            "status": (
                "Failed"
                if missing_delivery_dates > 0
                else "Passed"
            ),
        }
    )

    results.append(
        {
            "rule_name": (
                "Delay days must be zero or greater"
            ),
            "failed_records": int(
                invalid_delay_values
            ),
            "status": (
                "Failed"
                if invalid_delay_values > 0
                else "Passed"
            ),
        }
    )

    results.append(
        {
            "rule_name": (
                "Shipment ID must be unique"
            ),
            "failed_records": int(
                duplicate_shipment_ids
            ),
            "status": (
                "Failed"
                if duplicate_shipment_ids > 0
                else "Passed"
            ),
        }
    )

    return pd.DataFrame(results)