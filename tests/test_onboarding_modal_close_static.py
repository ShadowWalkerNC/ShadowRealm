"""Static regressions: onboarding setup modal must be able to close.

The Sprint 9 onboarding box previously set display:flex inline on
#onboarding-modal. That inline style beat .modal.hidden { display:none },
so Finish Setup (and a completed onboarding_completed flag) could not hide
the overlay.
"""

from pathlib import Path


_REPO = Path(__file__).resolve().parent.parent
_INDEX = (_REPO / "static" / "index.html").read_text(encoding="utf-8")
_APP = (_REPO / "static" / "app.js").read_text(encoding="utf-8")


def _onboarding_modal_tag() -> str:
    start = _INDEX.index('id="onboarding-modal"')
    # Walk back to the opening <div
    open_idx = _INDEX.rfind("<div", 0, start)
    close_idx = _INDEX.index(">", start) + 1
    return _INDEX[open_idx:close_idx]


def test_onboarding_modal_has_no_inline_display():
    tag = _onboarding_modal_tag()
    assert 'id="onboarding-modal"' in tag
    assert "class=" in tag and "modal" in tag and "hidden" in tag
    # Any inline display: (flex/block/etc.) wins over .modal.hidden.
    assert "display:" not in tag.lower()


def test_finish_setup_closes_modal_and_clears_inline_display():
    assert "closeOnboardingModal" in _APP
    assert "onboardingModal.classList.add('hidden')" in _APP
    assert "onboardingModal.style.removeProperty('display')" in _APP
    assert "Storage.set('onboarding_completed', 'true')" in _APP
    # Finish Setup handler must call the closer, not only toggle a class.
    finish_block_start = _APP.index("if (next2 && onboardingModal)")
    finish_block = _APP[finish_block_start : finish_block_start + 450]
    assert "closeOnboardingModal()" in finish_block
    assert "Storage.set('onboarding_completed', 'true')" in finish_block


def test_completed_onboarding_stays_closed_on_load():
    block_start = _APP.index("// Onboarding Wizard (Sprint 9)")
    block = _APP[block_start : block_start + 1200]
    assert "Storage.get('onboarding_completed')" in block
    assert "closeOnboardingModal()" in block
    assert "openOnboardingModal()" in block
