import importlib.util
import re
import sys
from pathlib import Path

from dash import Dash, Input, Output, State, dcc, html


ROOT_DIR = Path(__file__).resolve().parent
GAMES = {
    "Matching": ("Matching", "🧩 Matching"),
    "Jeopardy": ("Jeopardy", "📘 Jeopardy"),
    "Wheel": ("Wheel", "🎡 Wheel"),
    "FamilyFeud": ("FamilyFeud", "👨‍👩‍👧‍👦 Family Feud"),
    "GuessWho": ("GuessWho", "👤 Guess Who"),
    "QuoteGuess": ("QuoteGuess", "💭 Quote Guess"),
    "DoctrinalMastery": ("DoctrinalMastery", "📖 Doctrinal Mastery"),
}


def _snake_case_name(name):
    return re.sub(r"(?<!^)(?=[A-Z])", "_", name).lower()


def load_game_module(game_key, folder_name):
    game_dir = ROOT_DIR / folder_name
    file_name_candidates = [
        f"{_snake_case_name(folder_name)}_dash_app.py",
        f"{folder_name.lower()}_dash_app.py",
        "dash_app.py",
    ]
    file_path = next(
        (game_dir / file_name for file_name in file_name_candidates if (game_dir / file_name).exists()),
        None,
    )
    if file_path is None:
        dash_files = sorted(game_dir.glob("*_dash_app.py"))
        if dash_files:
            file_path = dash_files[0]
        else:
            raise FileNotFoundError(f"Unable to find a Dash app file in: {game_dir}")

    module_name = f"dash_game_{game_key.lower()}"

    # Remove cached local helpers so same-named modules in other games cannot leak across.
    for helper_path in game_dir.glob("*.py"):
        if helper_path.stem == "dash_app":
            continue
        cached_module = sys.modules.get(helper_path.stem)
        cached_path = getattr(cached_module, "__file__", None)
        if cached_path and Path(cached_path).resolve().parent == game_dir:
            del sys.modules[helper_path.stem]

    game_dir_text = str(game_dir)
    sys.path.insert(0, game_dir_text)
    try:
        spec = importlib.util.spec_from_file_location(module_name, file_path)
        if spec is None or spec.loader is None:
            raise ImportError(f"Unable to load Dash page module: {file_path}")
        module = importlib.util.module_from_spec(spec)
        sys.modules[module_name] = module
        spec.loader.exec_module(module)
        return module
    finally:
        sys.path.remove(game_dir_text)


page_modules = {
    game_key: load_game_module(game_key, folder_name)
    for game_key, (folder_name, _) in GAMES.items()
}

app = Dash(__name__, title="LDS Games Launcher", suppress_callback_exceptions=True)
server = app.server


app.layout = html.Div(
    [
        dcc.Store(id="dark-mode-state", data=False, storage_type="local"),
        html.Header(
            [
                html.Div(
                    [
                        html.H1("🎮 LDS Games Arcade"),
                        dcc.Dropdown(
                            id="game-selector",
                            options=[
                                {"label": "🏠 Home", "value": "Home"},
                                *[
                                    {"label": label, "value": game_key}
                                    for game_key, (_, label) in GAMES.items()
                                ],
                            ],
                            value="Home",
                            clearable=False,
                            style={"maxWidth": "420px"},
                        ),
                    ],
                    className="launcher-heading",
                ),
                html.Button(
                    [
                        html.Span(
                            html.Span(className="theme-toggle__thumb"),
                            className="theme-toggle__track",
                        ),
                        html.Span("Dark mode"),
                    ],
                    id="dark-mode-toggle",
                    n_clicks=0,
                    className="theme-toggle",
                    role="switch",
                    **{"aria-label": "Dark mode", "aria-checked": "false"},
                ),
            ],
            className="launcher-header",
        ),
        html.Main(id="game-content"),
    ],
    id="app-shell",
    className="app-shell",
    style={
        "fontFamily": "Arial, sans-serif",
        "width": "100%",
        "boxSizing": "border-box",
        "padding": "2rem",
    },
)


for page_module in page_modules.values():
    page_module.register_callbacks(app)


@app.callback(Output("game-content", "children"), Input("game-selector", "value"))
def render_game(game_key):
    if game_key == "Home":
        return html.Div("Select a game from the menu to begin.")
    return page_modules[game_key].layout()


@app.callback(
    Output("dark-mode-state", "data"),
    Input("dark-mode-toggle", "n_clicks"),
    State("dark-mode-state", "data"),
    prevent_initial_call=True,
)
def update_dark_mode(_clicks, is_dark):
    if not _clicks:
        return bool(is_dark)
    return not bool(is_dark)


@app.callback(
    Output("app-shell", "className"),
    Output("dark-mode-toggle", "aria-checked"),
    Input("dark-mode-state", "data"),
)
def apply_dark_mode(is_dark):
    return ("app-shell dark-mode" if is_dark else "app-shell", str(bool(is_dark)).lower())


if __name__ == "__main__":
    app.run(debug=True)
