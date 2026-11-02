"""Regression against observed spreadsheet formula outputs (not historical forecasts)."""
import pytest
from cfb_analytics.workbook_prediction import workbook_prediction


@pytest.mark.parametrize("home,away,hr,ar,neutral,spread,margin,model,shown,winner", [
    ("Akron","Ohio",-16.563226209,-6.051756742,False,12.5,-7.511469467,0.276702510,0.186029920,"Ohio"),
    ("Miami (OH)","Buffalo",-8.007965688,-14.397108698,False,-6.5,9.389143010,0.768715478,0.682985987,"Miami (OH)"),
    ("Massachusetts","Ball State",-16.014223710,-17.218991651,False,-4.5,4.204767941,0.631319062,0.629801605,"Massachusetts"),
    ("Sacramento State","Toledo",-21.040307152,-1.538097765,False,27.5,-16.502209386,0.108033652,0.037426357,"Toledo"),
    ("Eastern Michigan","Central Michigan",-12.643291894,-11.960623269,True,-1.5,-0.682668625,0.478181883,0.544165080,"Eastern Michigan"),
])
def test_workbook_observed_rows(home,away,hr,ar,neutral,spread,margin,model,shown,winner):
    result = workbook_prediction(home,away,hr,ar,neutral=neutral,closing_home_spread=spread)
    assert result.projected_home_margin == pytest.approx(margin,abs=1e-7)
    assert result.model_home_probability == pytest.approx(model,abs=1e-8)
    assert result.displayed_home_probability == pytest.approx(shown,abs=1e-8)
    assert result.displayed_winner == winner
