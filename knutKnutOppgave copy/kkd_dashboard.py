import os
import pickle
import numpy as np
import dash
from dash import dcc, html
from dash.dependencies import Input, Output, State
from pathlib import Path

# -------------------------------------------------------
# Paths
# -------------------------------------------------------
BASE = Path(__file__).parent
MODELS_DIR = BASE / "models"

# -------------------------------------------------------
# Load trained model and scalers
# -------------------------------------------------------
with open(MODELS_DIR / "price_model.pkl", "rb") as f:
    price_model = pickle.load(f)

with open(MODELS_DIR / "price_model_bias.pkl", "rb") as f:
    price_model_bias = pickle.load(f)

with open(MODELS_DIR / "scalers.pkl", "rb") as f:
    scalers = pickle.load(f)

# Price scaler info
price_scaler = scalers["price"]
X_mean_price = price_scaler["mean"]
X_std_price = price_scaler["std"]
numeric_features = price_scaler["numeric_features"]

# -------------------------------------------------------
# Month and Agent Definitions
# -------------------------------------------------------
MONTHS = [
    "jan", "feb", "march", "april", "may", "june",
    "july", "august", "september", "october", "november", "december"
]

AGENTS = [
    {"agent_id": "6c5ec2f26798484fb1031a7a31c08d73", "name": "Alice Vadasy"},
    {"agent_id": "3a547da007e04cbdb8ed7e36a5920ab5", "name": "Rhonda Bowers"},
    {"agent_id": "795dc3219c4548de8a06babe17e5312c", "name": "Pedro Sasser"},
    {"agent_id": "8e6475f796cd425cafc497e1a5c9474f", "name": "Porfirio Wueste"},
    {"agent_id": "32b554b9e556415b9c1a5f429cb86ea4", "name": "Donna Mcclintock"},
    {"agent_id": "19a0b5650c4d43619cbaeeac9cc7a20a", "name": "Frank Schmidt"},
    {"agent_id": "efef30ab07cd407a88aa48c424d5171a", "name": "John Rios"},
    {"agent_id": "b07e66765f334ca9970aaee99cffc5a8", "name": "Michael Hanners"},
    {"agent_id": "fff5808fd1564d4fafd32ae748479a2c", "name": "John Jimenez"},
    {"agent_id": "c4a0f434295d4e4e972b2512823d6c4a", "name": "Frank Scheetz"},
    {"agent_id": "d2bd04c4a79d409d8d692ca8eea96c7a", "name": "Donald Campbell"},
    {"agent_id": "f80b78e84ee54bdd9aff519346ba2f19", "name": "Kirsten Webb"},
    {"agent_id": "4ecaa44743f145529c682799a4ff7100", "name": "Michael Rowland"},
    {"agent_id": "5f0b7975f5bc42cd8a46f8c2cc0a7bc8", "name": "Charlotte Nodine"},
    {"agent_id": "9656ed14d6ea47fd84503af7e1be3e4e", "name": "Ann Perez"},
    {"agent_id": "48589954489f46239de57d1846b9c79b", "name": "Shirley Delrio"},
    {"agent_id": "cb7d8976bd0a4c98826b3344ac18cdea", "name": "Lucy Moffatt"},
    {"agent_id": "ebb2ffc4234b40ebb7bf9bdd9c92ad98", "name": "Gonzalo Ramos"},
    {"agent_id": "63f3d4cadbf944dca0e586711d33a70f", "name": "Cheryl Dunlap"},
    {"agent_id": "defb7dd2db4845baa9e94f9a38000913", "name": "Mary Chavez"},
    {"agent_id": "ef141ba69bf94741aa575623c7abc6d8", "name": "Pat Daniels"},
    {"agent_id": "fc8bd0d643b94de58c36d221f27b6f66", "name": "Johnnie Stanley"},
    {"agent_id": "36e5c7e1c1a5478287fc3c4ad91bc72c", "name": "Misty Wallace"},
    {"agent_id": "90ac6055bfd045adaf501fad965c6ea3", "name": "Gregory Dixon"}
]

AGENT_IDS = [a["agent_id"] for a in AGENTS]

# -------------------------------------------------------
# Categorical mapping
# -------------------------------------------------------
price_category_maps = {
    "sold_in_month": {m: i for i, m in enumerate(sorted(MONTHS))},
    "agent_id": {aid: i for i, aid in enumerate(sorted(AGENT_IDS))}
}

# -------------------------------------------------------
# Feature vector creation
# -------------------------------------------------------
def create_feature_vector(size, external_storage, lot_w, sold_month, agent_id):
    # scale numeric features
    numeric = np.array([size, external_storage, lot_w], float)
    numeric_scaled = (numeric - X_mean_price) / X_std_price

    # month one-hot
    month_oh = [0] * len(price_category_maps["sold_in_month"])
    month_idx = price_category_maps["sold_in_month"][sold_month]
    month_oh[month_idx] = 1

    # agent one-hot
    agent_oh = [0] * len(price_category_maps["agent_id"])
    agent_idx = price_category_maps["agent_id"][agent_id]
    agent_oh[agent_idx] = 1

    xs = np.hstack([numeric_scaled, month_oh, agent_oh])

    # Debug prints
    print("---- Feature Vector Debug ----")
    print(f"Numeric scaled: {numeric_scaled}")
    print(f"Month one-hot: {month_oh}")
    print(f"Agent one-hot: {agent_oh}")
    print(f"Full vector shape: {xs.shape}")
    print(f"Full vector sum: {xs.sum()}")
    print("------------------------------")

    return xs

# -------------------------------------------------------
# Predict function
# -------------------------------------------------------
def predict(theta, xs, bias):
    xs = xs.reshape(1, -1)
    log_price = np.dot(xs, theta).item() + bias
    return np.expm1(log_price)

def predict_price_model(size, external_storage, lot_w, sold_month, agent_id):
    xs = create_feature_vector(size, external_storage, lot_w, sold_month, agent_id)
    return predict(price_model, xs, price_model_bias)

# -------------------------------------------------------
# Dash App
# -------------------------------------------------------
app = dash.Dash(__name__)

app.layout = html.Div([
    html.H2("KKD Housing Price Predictor"),
    html.Label("Size (m²):"),
    dcc.Input(id="size", type="number", value=80),
    html.Br(), html.Br(),
    html.Label("External Storage (m²):"),
    dcc.Input(id="ext_storage", type="number", value=5),
    html.Br(), html.Br(),
    html.Label("Lot Width (meters):"),
    dcc.Input(id="lot_width", type="number", value=12),
    html.Br(), html.Br(),
    html.Label("Sold in Month:"),
    dcc.Dropdown(
        id="sold_month",
        options=[{"label": m.capitalize(), "value": m} for m in MONTHS],
        value="november"
    ),
    html.Br(), html.Br(),
    html.Label("Agent:"),
    dcc.Dropdown(
        id="agent",
        options=[{"label": a["name"], "value": a["agent_id"]} for a in AGENTS],
        value=AGENT_IDS[0]
    ),
    html.Br(),
    html.Button("Predict Price", id="predict-btn", n_clicks=0),
    html.H3("Predicted Price:"),
    html.Pre(id="price-output")
])

# -------------------------------------------------------
# Callback
# -------------------------------------------------------
@app.callback(
    Output("price-output", "children"),
    Input("predict-btn", "n_clicks"),
    State("size", "value"),
    State("ext_storage", "value"),
    State("lot_width", "value"),
    State("sold_month", "value"),
    State("agent", "value")
)
def ui_predict(n, size, ext, lot, month, agent_id):
    if n == 0:
        return "Click predict to see the price."
    price = predict_price_model(size, ext, lot, month, agent_id)
    return f"{price:,.2f} NOK"

# -------------------------------------------------------
if __name__ == "__main__":
    app.run(debug=True)
