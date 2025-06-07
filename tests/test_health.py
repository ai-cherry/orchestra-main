"""Basic health check tests."""

from orchestra_core.ping import ping, version


def test_ping():
    """Test basic ping function."""
    assert ping() == "pong"


def test_version():
    """Test version function."""
    assert version() == "0.1.0" 