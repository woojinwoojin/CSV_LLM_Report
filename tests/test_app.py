import pytest
from streamlit.testing.v1 import AppTest

from analysis import SUPERSTORE


@pytest.mark.skipif(not SUPERSTORE.path.exists(), reason="기본 데이터(data/) 없음")
def test_app_renders_default_dataset_without_errors():
    at = AppTest.from_file("../app.py", default_timeout=30).run()  # 이 파일 기준 상대 경로

    assert not at.exception
    assert not at.error
    assert [m.label for m in at.metric] == ["총 매출 (USD)", "총 이익 (USD)", "주문 수", "고객 수"]
    assert at.metric[2].value == "5,009"
    # 보고서는 버튼을 눌러야만 생성된다 (자동으로 API를 호출하지 않음)
    assert at.button[0].label == "보고서 생성"
