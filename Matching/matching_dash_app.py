import random
import time

from dash import ALL, Input, Output, State, ctx, dcc, html


SCRIPTURES = {
    "Moses 1:39": "“This is my work and my glory—to bring to pass the immortality and eternal life of man.”",
    "Moses 7:18": "“The Lord called his people Zion, because they were of one heart and one mind.”",
    "Abraham 2:9–11": "The Lord promised Abraham that his seed would “bear this ministry and Priesthood unto all nations.”",
    "Abraham 3:22–23": "As spirits we “were organized before the world was.”",
    "Genesis 1:26–27": "“God created man in his own image.”",
    "Genesis 2:24": "“A man … shall cleave unto his wife: and they shall be one.”",
    "Genesis 39:9": "“How then can I do this great wickedness, and sin against God?”",
    "Exodus 20:3–17": "The Ten Commandments",
    "Joshua 24:15": "“Choose you this day whom ye will serve.”",
    "Psalm 24:3–4": "“Who shall stand in his holy place? He that hath clean hands, and a pure heart.”",
    "Proverbs 3:5–6": "“Trust in the Lord with all thine heart … and he shall direct thy paths.”",
    "Isaiah 1:18": "“Though your sins be as scarlet, they shall be as white as snow.”",
    "Isaiah 5:20": "“Woe unto them that call evil good, and good evil.”",
    "Isaiah 29:13–14": "The restoration of the gospel is “a marvellous work and a wonder.”",
    "Isaiah 53:3–5": "“Surely [Jesus Christ] hath borne our griefs, and carried our sorrows.”",
    "Isaiah 58:6–7": "The blessings of a proper fast",
    "Isaiah 58:13–14": "“Turn away … from doing thy pleasure on my holy day; and call the sabbath a delight.”",
    "Jeremiah 1:4–5": "“Before I formed thee in the belly … I ordained thee a prophet unto the nations.”",
    "Ezekiel 3:16–17": "The prophet is “a watchman unto the house of Israel.”",
    "Ezekiel 37:15–17": "The Bible and the Book of Mormon “shall become one in thine hand.”",
    "Daniel 2:44–45": "God shall “set up a kingdom, which shall never be destroyed.”",
    "Amos 3:7": "“The Lord God … revealeth his secret unto his servants the prophets.”",
    "Malachi 3:8–10": "The blessings of paying tithing",
    "Malachi 4:5–6": "Elijah “shall turn … the heart of the children to their fathers.”",
}

TEAM_COLORS = ["#FF4B4B", "#007BFF", "#2ECC71", "#F4B400"]


def _new_game(pair_count=6, team_count=4):
    selected = random.sample(list(SCRIPTURES.items()), int(pair_count))
    cards = []
    for reference, phrase in selected:
        cards.extend([[reference, "reference"], [phrase, "phrase"]])
    random.shuffle(cards)
    return {
        "cards": cards,
        "revealed": [],
        "matched": [],
        "matched_by_team": {},
        "turns": 0,
        "team_scores": [0] * int(team_count),
        "current_team": random.randrange(int(team_count)),
        "flip_timer": None,
        "all_revealed": False,
        "pair_count": int(pair_count),
        "team_count": int(team_count),
    }


def _card_letter(index):
    if index < 26:
        return chr(65 + index)
    return chr(65 + (index % 26)) * ((index // 26) + 1)


def _is_match(cards, first, second):
    card_a = cards[first][0]
    card_b = cards[second][0]
    return SCRIPTURES.get(card_a) == card_b or SCRIPTURES.get(card_b) == card_a


def _render_board(game):
    cards = game["cards"]
    revealed = set(game["revealed"])
    matched = set(game["matched"])
    rows = []
    for start in range(0, len(cards), 6):
        cells = []
        for index in range(start, min(start + 6, len(cards))):
            card_text = cards[index][0]
            if index in matched:
                team = game["matched_by_team"].get(str(index), 0)
                content = html.Div(
                    card_text,
                    style={
                        "fontSize": "1.1rem",
                        "textAlign": "center",
                        "color": TEAM_COLORS[team],
                        "padding": "1rem 0.35rem",
                        "overflowWrap": "anywhere",
                    },
                )
            elif game["all_revealed"] or index in revealed:
                content = html.Div(
                    card_text,
                    style={
                        "fontSize": "1.1rem",
                        "textAlign": "center",
                        "padding": "1rem 0.35rem",
                        "overflowWrap": "anywhere",
                    },
                )
            else:
                content = html.Button(
                    _card_letter(index),
                    id={"type": "matching-card", "index": index},
                    n_clicks=0,
                    disabled=game["flip_timer"] is not None or game["all_revealed"],
                    style={
                        "width": "100%",
                        "minHeight": "100px",
                        "fontSize": "1.25rem",
                        "whiteSpace": "normal",
                    },
                )
            cells.append(html.Div(content, style={"flex": "1 1 15%", "minWidth": "130px"}))
        rows.append(html.Div(cells, style={"display": "flex", "gap": "0.75rem", "marginBottom": "1rem"}))
    return rows


def _render_scores(game):
    scores = game["team_scores"]
    return [
        html.Div(
            f"Team {index + 1}: {score}" + (" ⬅️" if index == game["current_team"] else ""),
            style={
                "color": TEAM_COLORS[index],
                "fontSize": "1.4rem",
                "fontWeight": "bold",
                "textAlign": "center",
                "flex": "1",
            },
        )
        for index, score in enumerate(scores)
    ]


def _render_status(game):
    children = [
        html.H3(f"Current turn: Team {game['current_team'] + 1}"),
        html.Div(f"Turns taken: {game['turns']}"),
    ]
    if len(game["matched"]) == len(game["cards"]):
        winner = max(range(len(game["team_scores"])), key=game["team_scores"].__getitem__)
        children.extend(
            [
                html.H3("🎉 Game Over! All pairs matched!", style={"color": "#16803c"}),
                html.Div(f"🏆 Winner: Team {winner + 1} with {game['team_scores'][winner]} points!"),
            ]
        )
    return children


def layout():
    game = _new_game()
    return html.Div(
        [
            dcc.Store(id="matching-state", data=game, storage_type="session"),
            dcc.Interval(id="matching-flip-interval", interval=250, disabled=True),
            html.H1("🧩 Scripture Match"),
            html.Div(
                [
                    html.Label("Number of scripture pairs:"),
                    dcc.Slider(
                        id="matching-pair-count",
                        min=6,
                        max=len(SCRIPTURES),
                        step=1,
                        value=6,
                        marks={6: "6", len(SCRIPTURES): str(len(SCRIPTURES))},
                        tooltip={"placement": "bottom", "always_visible": True},
                    ),
                    html.Label("Number of teams:", style={"marginTop": "1rem", "display": "block"}),
                    dcc.Slider(
                        id="matching-team-count",
                        min=2,
                        max=4,
                        step=1,
                        value=4,
                        marks={2: "2", 3: "3", 4: "4"},
                        tooltip={"placement": "bottom", "always_visible": True},
                    ),
                    html.Div(
                        [
                            html.Button("🔁 Start New Game", id="matching-new-game", n_clicks=0),
                            html.Button("👁️ Reveal All", id="matching-reveal", n_clicks=0),
                            html.Button("🙈 Hide All", id="matching-hide", n_clicks=0),
                            html.Button("🔁 Restart Game", id="matching-restart", n_clicks=0),
                            html.Button("⏭️ Next Guess", id="matching-reset-guess", n_clicks=0, disabled=True),
                        ],
                        style={"display": "flex", "gap": "0.5rem", "flexWrap": "wrap", "margin": "1rem 0"},
                    ),
                ],
                style={"maxWidth": "700px"},
            ),
            html.Div(id="matching-status", children=_render_status(game)),
            html.Div(id="matching-board", children=_render_board(game)),
            html.Hr(),
            html.Div(
                id="matching-scores",
                children=_render_scores(game),
                style={"display": "flex", "gap": "0.75rem", "flexWrap": "wrap"},
            ),
        ],
        style={"fontFamily": "Arial, sans-serif"},
    )


def register_callbacks(app):
    @app.callback(
        Output("matching-state", "data"),
        Output("matching-board", "children"),
        Output("matching-status", "children"),
        Output("matching-scores", "children"),
        Output("matching-flip-interval", "disabled"),
        Output("matching-reset-guess", "disabled"),
        Input({"type": "matching-card", "index": ALL}, "n_clicks"),
        Input("matching-new-game", "n_clicks"),
        Input("matching-reveal", "n_clicks"),
        Input("matching-hide", "n_clicks"),
        Input("matching-restart", "n_clicks"),
        Input("matching-reset-guess", "n_clicks"),
        Input("matching-flip-interval", "n_intervals"),
        State("matching-pair-count", "value"),
        State("matching-team-count", "value"),
        State("matching-state", "data"),
        prevent_initial_call=True,
    )
    def update_game(_card_clicks, _new, _reveal, _hide, _restart, _reset_guess, _ticks, pair_count, team_count, data):
        game = data or _new_game(pair_count, team_count)
        trigger = ctx.triggered_id

        if trigger == "matching-new-game" or trigger == "matching-restart":
            game = _new_game(pair_count, team_count)
        elif trigger == "matching-reveal":
            game["all_revealed"] = True
            game["revealed"] = list(range(len(game["cards"])))
        elif trigger == "matching-hide":
            game["all_revealed"] = False
            game["revealed"] = []
        elif trigger == "matching-flip-interval" or trigger == "matching-reset-guess":
            if game["flip_timer"] and (
                trigger == "matching-reset-guess" or time.time() - game["flip_timer"] >= 3
            ):
                game["revealed"] = []
                game["current_team"] = (game["current_team"] + 1) % len(game["team_scores"])
                game["flip_timer"] = None
        elif isinstance(trigger, dict) and trigger.get("type") == "matching-card":
            index = trigger["index"]
            if (
                index not in game["matched"]
                and index not in game["revealed"]
                and game["flip_timer"] is None
                and not game["all_revealed"]
            ):
                game["revealed"].append(index)
                if len(game["revealed"]) == 2:
                    first, second = game["revealed"]
                    game["turns"] += 1
                    if _is_match(game["cards"], first, second):
                        team = game["current_team"]
                        game["matched"].extend([first, second])
                        game["matched_by_team"][str(first)] = team
                        game["matched_by_team"][str(second)] = team
                        game["team_scores"][team] += 1
                        game["revealed"] = []
                    else:
                        game["flip_timer"] = time.time()

        return (
            game,
            _render_board(game),
            _render_status(game),
            _render_scores(game),
            game["flip_timer"] is None,
            game["flip_timer"] is None,
        )
