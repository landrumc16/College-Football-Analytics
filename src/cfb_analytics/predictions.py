from dataclasses import dataclass
from .model import confidence_label, market_home_win_probability, model_home_margin, win_probability_from_rating_gap


@dataclass(frozen=True)
class Prediction:
    home_margin: float
    model_home_probability: float
    published_home_probability: float
    winner: str
    confidence: str


def predict(home: str, away: str, home_rating: float, away_rating: float, *, neutral=False, closing_home_spread=None, home_field_advantage=3.0, model_scale=18.0, market_scale=19.5) -> Prediction:
    margin = model_home_margin(home_rating, away_rating, neutral=neutral, home_field_advantage=home_field_advantage)
    model_prob = win_probability_from_rating_gap(margin, model_scale)
    published = model_prob if closing_home_spread is None else market_home_win_probability(closing_home_spread, market_scale)
    return Prediction(margin, model_prob, published, home if published >= 0.5 else away, confidence_label(published))
