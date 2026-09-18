"""Provider scaffolding tests: adding a new network stays a one-command job."""
import pytest
from django.core.management import call_command

from apps.adminpanel.scaffolding import (
    adapter_path_for,
    class_name_for,
    render_adapter,
)

pytestmark = pytest.mark.django_db


def test_class_and_path_helpers():
    assert class_name_for("adgem") == "Adgem"
    assert class_name_for("my-network") == "MyNetwork"
    assert adapter_path_for("cpa", "adgem") == "apps.cpa.providers.adgem.AdgemAdapter"
    assert (
        adapter_path_for("payment", "easy-paisa")
        == "apps.payments.providers.easy_paisa.EasyPaisaAdapter"
    )


def test_cpa_template_contains_interface():
    content = render_adapter("cpa", "adgem", "AdGem")

    assert "class AdgemAdapter(CPAProviderAdapter)" in content
    assert 'code = "adgem"' in content
    assert "def get_offers" in content
    assert "def process_postback" in content
    assert "def validate_signature" in content
    assert "ADGEM_API_KEY" in content


def test_survey_and_payment_templates():
    survey = render_adapter("survey", "cpx", "CPX Research")
    assert "class CpxAdapter(SurveyProviderAdapter)" in survey
    assert "def get_surveys" in survey

    payment = render_adapter("payment", "easypaisa", "EasyPaisa")
    assert "class EasypaisaAdapter(PaymentProviderAdapter)" in payment
    assert "def create_payment" in payment
    assert "def verify_webhook" in payment


def test_command_dry_run_prints_without_writing(capsys):
    call_command("scaffold_provider", "cpa", "adgem", "--name", "AdGem", "--dry-run")

    output = capsys.readouterr().out
    assert "class AdgemAdapter(CPAProviderAdapter)" in output


def test_command_writes_file_and_reports_adapter_path(monkeypatch, tmp_path, capsys):
    monkeypatch.setattr(
        "apps.adminpanel.management.commands.scaffold_provider.target_path",
        lambda kind, code: tmp_path / f"{code}.py",
    )

    call_command("scaffold_provider", "cpa", "newco", "--name", "NewCo")

    written = tmp_path / "newco.py"
    assert written.is_file()
    assert "class NewcoAdapter(CPAProviderAdapter)" in written.read_text(encoding="utf-8")

    output = capsys.readouterr().out
    assert "adapter_path = apps.cpa.providers.newco.NewcoAdapter" in output


def test_command_never_overwrites_existing_file(monkeypatch, tmp_path, capsys):
    existing = tmp_path / "adgem.py"
    existing.write_text("do not touch", encoding="utf-8")
    monkeypatch.setattr(
        "apps.adminpanel.management.commands.scaffold_provider.target_path",
        lambda kind, code: existing,
    )

    call_command("scaffold_provider", "cpa", "adgem")

    assert existing.read_text(encoding="utf-8") == "do not touch"
    assert "already exists" in capsys.readouterr().err
