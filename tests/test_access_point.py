from src.connection.access_point import parse_nmcli_terse, wifi_qr_payload


def test_parse_nmcli_terse_unescapes_values() -> None:
    output = "802-11-wireless.ssid:Bar\\:Berry\n802-11-wireless-security.psk:a\\\\b\nGENERAL.STATE:activated\n"
    assert parse_nmcli_terse(output) == {
        "802-11-wireless.ssid": "Bar:Berry",
        "802-11-wireless-security.psk": "a\\b",
        "GENERAL.STATE": "activated",
    }


def test_wifi_qr_payload_escapes_special_characters() -> None:
    assert wifi_qr_payload("Bar;Berry", r'p:a,s"s\1') == r"WIFI:T:WPA;S:Bar\;Berry;P:p\:a\,s\"s\\1;;"
