import pytest
from main import run_bc, run_login, run_workorder


def test_bc_runs():
    # Should complete without raising
    run_bc()


def test_login_runs():
    run_login()


def test_workorder_runs():
    run_workorder()
