import pytest
import yaml

from cola.config import Config, ConfigClient, ConfigRegistry

TEST_CONFIG = {
    "topa": {
        "b": 1,
        "c": 2,
        "d": {
            "e": "a value",
        },
    },
    "topb": "b",
}

TEST_CONFIG_FLAT = {
    "topa.b": 1,
    "topa.c": 2,
    "topa.d.e": "a value",
    "topb": "b",
}

TEST_CONFIG_BAD_KEYS = [
    "BADKEY",
    "topa.BADKEY",
    "topa.d.BADKEY",
    "topa.e.BADKEY",
    "topa.e.BADKEY.WORSE",
]


@pytest.fixture
def config_file(tmp_path):
    f = tmp_path / "config.yaml"
    with f.open("w") as fh:
        yaml.dump(TEST_CONFIG, fh)
    return f


@pytest.fixture
def test_config(config_file):
    return Config(file=config_file)


def test_config_init(config_file):
    config1 = Config(file=config_file)
    config2 = Config(config_data=TEST_CONFIG)
    assert config1.config == config2.config
    assert config1.config == TEST_CONFIG


def test_config_save_no_file():
    config = Config(config_data=TEST_CONFIG)
    config.save()
    assert config.file is None


def test_config_save_ok(config_file):
    config = Config(file=config_file)
    config.save()
    with config_file.open() as f:
        config_data = yaml.safe_load(f)
    assert config_data == TEST_CONFIG


@pytest.mark.parametrize(
    "key, expected",
    [
        ("topa.b", 1),
        ("topa.d.e", "a value"),
        ("topa.d", {"e": "a value"}),
        ("topb", "b"),
    ],
)
def test_keys(test_config, key, expected):
    assert test_config.get(key) == expected


@pytest.mark.parametrize("bad_key", TEST_CONFIG_BAD_KEYS)
def test_get_strict_bad_key_raises(test_config, bad_key):
    with pytest.raises(KeyError, match=f"'{bad_key}'"):
        test_config.get_strict(bad_key)


@pytest.mark.parametrize("bad_key", TEST_CONFIG_BAD_KEYS)
def test_get_bad_key_gives_none(test_config, bad_key):
    assert test_config.get(bad_key) is None


def test_set():
    cfg = Config()
    for key, value in TEST_CONFIG_FLAT.items():
        cfg.set(key, value)
    assert cfg.config == TEST_CONFIG


@pytest.mark.parametrize(
    "key, expected",
    [(bad_key, False) for bad_key in TEST_CONFIG_BAD_KEYS] + [(good_key, True) for good_key in TEST_CONFIG_FLAT.keys()],
)
def test_has(test_config, key, expected):
    assert test_config.has(key) == expected


@pytest.mark.parametrize("bad_key", TEST_CONFIG_BAD_KEYS)
def test_delete_bad_keys(test_config, bad_key):
    with pytest.raises(KeyError, match=f"'{bad_key}'"):
        test_config.delete(bad_key)


def test_delete(test_config):
    test_config.delete("topa.b")
    assert test_config.config == {"topa": {"c": 2, "d": {"e": "a value"}}, "topb": "b"}
    test_config.delete("topb")
    assert test_config.config == {"topa": {"c": 2, "d": {"e": "a value"}}}
    test_config.delete("topa.d")
    assert test_config.config == {"topa": {"c": 2}}
    test_config.delete("topa.c")
    assert test_config.config == {}


@pytest.mark.parametrize(
    "key, expected",
    [
        ("topa", {"topb": "b"}),
        (
            "topa.c",
            {"topa": {"b": 1, "d": {"e": "a value"}}, "topb": "b"},
        ),
        (
            "topa.d.e",
            {"topa": {"b": 1, "c": 2}, "topb": "b"},
        ),
    ],
)
def test_config_delete(key, expected, config_file):
    config = Config(file=config_file)
    config.delete(key)
    assert config.config == expected


# --- Registry tests ---


REGISTRY_YAML = """\
version: 1
keys:
  top_key:
    description: A top-level key
    example: "value"
  group1:
    description: A group
    keys:
      sub_key:
        description: A grouped key
        example: "sub_value"
"""


@pytest.fixture
def registry_file(tmp_path):
    f = tmp_path / "registry.yml"
    f.write_text(REGISTRY_YAML)
    return f


def test_registry_load(registry_file):
    registry = ConfigRegistry.load(registry_file)
    assert registry.has_key("top_key")
    assert registry.has_key("group1.sub_key")
    assert not registry.has_key("nonexistent")
    assert not registry.has_key("group1.nonexistent")


def test_registry_get_key(registry_file):
    registry = ConfigRegistry.load(registry_file)
    key = registry.get_key("top_key")
    assert key.description == "A top-level key"
    key = registry.get_key("group1.sub_key")
    assert key.description == "A grouped key"


def test_registry_missing_file(tmp_path):
    registry = ConfigRegistry.load(tmp_path / "nonexistent.yml")
    assert not registry.has_key("anything")


# --- ConfigClient tests ---


def test_config_client(monkeypatch, tmp_path):
    # Create a config file
    config_file = tmp_path / "config.yml"
    config_file.write_text(yaml.dump({"mail": {"server": "smtp.test.com", "port": "587"}}))

    config = Config(file=config_file)
    client = ConfigClient()
    client.wants_entry("mail.server", description="SMTP server")
    client.wants_entry("mail.port", description="SMTP port")
    client.wants_entry("mail.from", description="From address", default="noreply@test.com")

    result = client.get(config=config)
    assert result.mail_server == "smtp.test.com"
    assert result.mail_port == "587"
    assert result.mail_from == "noreply@test.com"


def test_config_client_missing_key_raises():
    config = Config(config_data={})
    client = ConfigClient()
    client.wants_entry("missing.key")

    with pytest.raises(KeyError):
        client.get(config=config)
