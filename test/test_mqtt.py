# Your test file (e.g., test_my_integration.py)

import pytest


# This test will NOT be marked
def test_basic_functionality():
    assert 1 + 1 == 2


# This test WILL be marked with 'target_machine'
@pytest.mark.target_machine
def test_interaction_with_haos():
    # This test requires running on the target machine (haos)
    # because it interacts with something specific to that environment.
    print("Running test that requires haos environment")
    # ... your test logic here ...


# Another test that will NOT be marked
def test_data_processing():
    data = [1, 2, 3]
    assert sum(data) == 6
