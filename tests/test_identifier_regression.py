from backend.privacy import Detector, leak_check
import json


def test_random_handles_are_not_numeric_pii():
    for value in [
        "e_ab4111111111111111cd",
        "s_9876510001482913737abcd",
        "e_abcdef234567890123abcdef",
    ]:
        assert leak_check(json.dumps({"id": value}).encode(), ["737"], Detector())
