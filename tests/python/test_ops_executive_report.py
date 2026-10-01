# -*- coding: utf-8 -*-
"""Test suite for Javis AI Executive Report & Strategic Audit Engine."""
import sys
from pathlib import Path

# Add server directory to sys.path
server_dir = Path(__file__).resolve().parent.parent.parent / "server"
if str(server_dir) not in sys.path:
    sys.path.insert(0, str(server_dir))

import ops_report
import ops_order_store


def test_generate_executive_report():
    report = ops_report.generate_executive_report(period="today")
    assert report["ok"] is True
    assert "summary" in report
    assert "health_score" in report["summary"]
    assert 0 <= report["summary"]["health_score"] <= 100
    assert "deep_dive" in report
    assert len(report["deep_dive"]["facts"]) >= 3
    assert len(report["deep_dive"]["signals"]) >= 2
    assert len(report["deep_dive"]["inferences"]) >= 2
    assert len(report["deep_dive"]["actions"]) >= 3
    assert "formatted_text" in report
    assert "cskh_evaluation" in report


def test_ops_order_store_list_shipments():
    shipments = ops_order_store.list_shipments(limit=10)
    assert isinstance(shipments, list)


def test_send_executive_report():
    res = ops_report.send_executive_report_to_owner(channel="telegram", period="today")
    assert res["ok"] is True
    assert "telegram" in res["channel"]
    assert len(res["preview"]) > 50


def main():
    test_generate_executive_report()
    test_ops_order_store_list_shipments()
    test_send_executive_report()
    print("OK - test_ops_executive_report: all passed")


if __name__ == "__main__":
    main()

