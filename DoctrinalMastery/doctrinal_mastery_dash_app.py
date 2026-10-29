"""Dash page for the 2-Team Doctrinal Mastery scripture & reference match game."""

import json
import random
import re

from dash import ALL, Input, Output, State, ctx, dcc, html

PREFIX = "dm"

VERSES = [
    {
        "reference": "Moses 1:39",
        "source": "Pearl of Great Price",
        "text": "For behold, this is my work and my glory—to bring to pass the immortality and eternal life of man.",
        "blanks": ["behold", "work", "glory", "bring", "pass", "immortality", "eternal", "life", "man", "this"],
    },
    {
        "reference": "Moses 7:18",
        "source": "Pearl of Great Price",
        "text": "And the Lord called his people Zion, because they were of one heart and one mind, and dwelt in righteousness; and there was no poor among them.",
        "blanks": ["Lord", "people", "Zion", "heart", "mind", "dwelt", "righteousness", "poor", "among", "called"],
    },
    {
        "reference": "Abraham 2:9-11",
        "source": "Pearl of Great Price",
        "text": "And I will make of thee a great nation, and I will bless thee above measure, and make thy name great among all nations, and thou shalt be a blessing unto thy seed after thee, that in their hands they shall bear this ministry and Priesthood unto all nations; And I will bless them through thy name; for as many as receive this Gospel shall be called after thy name, and shall be accounted thy seed, and shall rise up and bless thee, as their father; And I will bless them that bless thee, and curse them that curse thee; and in thee (that is, in thy Priesthood) and in thy seed (that is, thy Priesthood), for I give unto thee a promise that this right shall continue in thee, and in thy seed after thee (that is to say, the literal seed, or the seed of the body) shall all the families of the earth be blessed, even with the blessings of the Gospel, which are the blessings of salvation, even of life eternal.",
        "blanks": ["make", "nation", "bless", "measure", "name", "great", "seed", "Priesthood", "receive", "promise"],
    },
    {
        "reference": "Abraham 3:22-23",
        "source": "Pearl of Great Price",
        "text": "Now the Lord had shown unto me, Abraham, the intelligences that were organized before the world was; and among all these there were many of the noble and great ones; And God saw these souls that they were good, and he stood in the midst of them, and he said: These I will make my rulers; for he stood among those that were spirits, and he saw that they were good; and he said unto me: Abraham, thou art one of them; thou wast chosen before thou wast born.",
        "blanks": ["Lord", "showed", "organized", "world", "many", "noble", "good", "midst", "rulers", "chosen"],
    },
    {
        "reference": "Genesis 1:26-27",
        "source": "Old Testament",
        "text": "And God said, Let us make man in our image, after our likeness: and let them have dominion over the fish of the sea, and over the fowl of the air, and over the cattle, and over all the earth, and over every creeping thing that creepeth upon the earth. So God created man in his own image, in the image of God created he him; male and female created he them.",
        "blanks": ["God", "make", "image", "likeness", "dominion", "earth", "creeping", "created", "male", "female"],
    },
    {
        "reference": "Genesis 2:24",
        "source": "Old Testament",
        "text": "Therefore shall a man leave his father and his mother, and shall cleave unto his wife: and they shall be one flesh.",
        "blanks": ["man", "leave", "father", "mother", "cleave", "wife", "one", "flesh", "shall", "Therefore"],
    },
    {
        "reference": "Genesis 39:9",
        "source": "Old Testament",
        "text": "There is none greater in this house than I; neither hath he kept back any thing from me but thee, because thou art his wife: how then can I do this great wickedness, and sin against God?",
        "blanks": ["greater", "house", "kept", "back", "thing", "wife", "great", "wickedness", "sin", "God"],
    },
    {
        "reference": "Exodus 20:3–17",
        "source": "Old Testament",
        "text": "Thou shalt have no other gods before me. Thou shalt not make unto thee any graven image. Thou shalt not take the name of the Lord thy God in vain. Remember the sabbath day, to keep it holy. Honour thy father and thy mother: that thy days may be long upon the land. Thou shalt not kill. Thou shalt not commit adultery. Thou shalt not steal. Thou shalt not bear false witness against thy neighbour. Thou shalt not covet any thing that is thy neighbour’s.",
        "blanks": ["gods", "graven", "image", "Lord", "sabbath", "holy", "father", "mother", "witness", "neighbour's"],
    },
    {
        "reference": "Joshua 24:15",
        "source": "Old Testament",
        "text": "And if it seem evil unto you to serve the Lord, choose you this day whom ye will serve; whether the gods which your fathers served that were on the other side of the flood, or the gods of the Amorites, in whose land ye dwell: but as for me and my house, we will serve the Lord.",
        "blanks": ["seem", "evil", "serve", "Lord", "choose", "gods", "fathers", "flood", "dwell", "house"],
    },
    {
        "reference": "Psalm 24:3–4",
        "source": "Old Testament",
        "text": "Who shall ascend into the hill of the Lord? or who shall stand in his holy place? He that hath clean hands, and a pure heart; who hath not lifted up his soul unto vanity, nor sworn deceitfully.",
        "blanks": ["ascend", "hill", "Lord", "stand", "holy", "clean", "hands", "pure", "heart", "vanity"],
    },
    {
        "reference": "Proverbs 3:5–6",
        "source": "Old Testament",
        "text": "Trust in the Lord with all thine heart; and lean not unto thine own understanding. In all thy ways acknowledge him, and he shall direct thy paths.",
        "blanks": ["Trust", "Lord", "heart", "lean", "understanding", "ways", "acknowledge", "direct", "paths", "thine"],
    },
    {
        "reference": "Isaiah 1:18",
        "source": "Old Testament",
        "text": "Come now, and let us reason together, saith the Lord: though your sins be as scarlet, they shall be as white as snow; though they be red like crimson, they shall be as wool.",
        "blanks": ["reason", "together", "Lord", "sins", "scarlet", "white", "snow", "red", "crimson", "wool"],
    },
    {
        "reference": "Isaiah 5:20",
        "source": "Old Testament",
        "text": "Woe unto them that call evil good, and good evil; that put darkness for light, and light for darkness; that put bitter for sweet, and sweet for bitter!",
        "blanks": ["Woe", "call", "evil", "good", "darkness", "light", "bitter", "sweet", "put", "them"],
    },
    {
        "reference": "Isaiah 29:13–14",
        "source": "Old Testament",
        "text": "Wherefore the Lord said, Forasmuch as this people draw near me with their mouth, and with their lips do honour me, but have removed their heart far from me, and their fear toward me is taught by the precept of men: Therefore, behold, I will proceed to do a marvellous work among this people, even a marvellous work and a wonder: for the wisdom of their wise men shall perish, and the understanding of their prudent men shall be hid.",
        "blanks": ["mouth", "lips", "honour", "heart", "precept", "marvellous", "work", "wonder", "wisdom", "understanding"],
    },
    {
        "reference": "Isaiah 53:3–5",
        "source": "Old Testament",
        "text": "He is despised and rejected of men; a man of sorrows, and acquainted with grief: and we hid as it were our faces from him; he was despised, and we esteemed him not. Surely he hath borne our griefs, and carried our sorrows: yet we did esteem him stricken, smitten of God, and afflicted. But he was wounded for our transgressions, he was bruised for our iniquities: the chastisement of our peace was upon him; and with his stripes we are healed.",
        "blanks": ["despised", "rejected", "sorrows", "grief", "stricken", "smitten", "wounded", "transgressions", "iniquities", "healed"],
    },
    {
        "reference": "Isaiah 58:6–7",
        "source": "Old Testament",
        "text": "Is not this the fast that I have chosen? to loose the bands of wickedness, to undo the heavy burdens, and to let the oppressed go free, and that ye break every yoke? Is it not to deal thy bread to the hungry, and that thou bring the poor that are cast out to thy house? when thou seest the naked, that thou cover him; and that thou hide not thyself from thine own flesh?",
        "blanks": ["fast", "loose", "wickedness", "burdens", "oppressed", "break", "yoke", "hungry", "poor", "naked"],
    },
    {
        "reference": "Isaiah 58:13–14",
        "source": "Old Testament",
        "text": "If thou turn away thy foot from the sabbath, from doing thy pleasure on my holy day; and call the sabbath a delight, the holy of the Lord, honourable; and shalt honour him, not doing thine own ways, nor finding thine own pleasure, nor speaking thine own words: Then shalt thou delight thyself in the Lord; and I will cause thee to ride upon the high places of the earth, and feed thee with the heritage of Jacob thy father: for the mouth of the Lord hath spoken it.",
        "blanks": ["sabbath", "pleasure", "holy", "delight", "honourable", "honour", "words", "ride", "heritage", "mouth"],
    },
    {
        "reference": "Jeremiah 1:4–5",
        "source": "Old Testament",
        "text": "Then the word of the Lord came unto me, saying, Before I formed thee in the belly I knew thee; and before thou camest forth out of the womb I sanctified thee, and I ordained thee a prophet unto the nations.",
        "blanks": ["word", "Lord", "formed", "belly", "knew", "womb", "sanctified", "ordained", "prophet", "nations"],
    },
    {
        "reference": "Ezekiel 3:16–17",
        "source": "Old Testament",
        "text": "And it came to pass at the end of seven days, that the word of the Lord came unto me, saying, Son of man, I have made thee a watchman unto the house of Israel: therefore hear the word at my mouth, and give them warning from me.",
        "blanks": ["pass", "seven", "days", "word", "Lord", "watchman", "Israel", "hear", "mouth", "warning"],
    },
    {
        "reference": "Ezekiel 37:15–17",
        "source": "Old Testament",
        "text": "Moreover, thou son of man, take thee one stick, and write upon it, For Judah, and for the children of Israel his companions: then take another stick, and write upon it, For Joseph, the stick of Ephraim, and for all the house of Israel his companions: And join them one to another into one stick; and they shall become one in thine hand.",
        "blanks": ["stick", "write", "Judah", "children", "Israel", "Joseph", "Ephraim", "house", "join", "hand"],
    },
    {
        "reference": "Daniel 2:44–45",
        "source": "Old Testament",
        "text": "And in the days of these kings shall the God of heaven set up a kingdom, which shall never be destroyed: and the kingdom shall not be left to other people, but it shall break in pieces and consume all these kingdoms, and it shall stand for ever.",
        "blanks": ["kings", "God", "heaven", "kingdom", "destroyed", "people", "break", "pieces", "consume", "stand"],
    },
    {
        "reference": "Amos 3:7",
        "source": "Old Testament",
        "text": "Surely the Lord God will do nothing, but he revealeth his secret unto his servants the prophets.",
        "blanks": ["Surely", "Lord", "God", "nothing", "revealeth", "secret", "servants", "prophets", "will", "unto"],
    },
    {
        "reference": "Malachi 3:8–10",
        "source": "Old Testament",
        "text": "Will a man rob God? Yet ye have robbed me. But ye say, Wherein have we robbed thee? In tithes and offerings. Ye are cursed with a curse: for ye have robbed me, even this whole nation. Bring ye all the tithes into the storehouse, that there may be meat in mine house, and prove me now herewith, saith the Lord of hosts, if I will not open you the windows of heaven, and pour you out a blessing, that there shall not be room enough to receive it.",
        "blanks": ["rob", "God", "tithes", "offerings", "cursed", "storehouse", "windows", "heaven", "pour", "blessing"],
    },
    {
        "reference": "Malachi 4:5–6",
        "source": "Old Testament",
        "text": "Behold, I will send you Elijah the prophet before the coming of the great and dreadful day of the Lord: And he shall turn the heart of the fathers to the children, and the heart of the children to their fathers, lest I come and smite the earth with a curse.",
        "blanks": ["Elijah", "prophet", "dreadful", "turn", "heart", "fathers", "children", "smite", "earth", "curse"],
    },
]

# List of all 24 scripture references sorted for dropdown selection
ALL_REFERENCES = sorted([v["reference"] for v in VERSES])


def _new_game_state():
    verse_indices = list(range(len(VERSES)))
    random.shuffle(verse_indices)  # Randomize scripture sequence for this game

    first_verse_index = verse_indices[0]
    initial_shuffled = list(VERSES[first_verse_index]["blanks"])
    random.shuffle(initial_shuffled)

    return {
        "initialized": True,
        "index": 0,
        "verse_order": verse_indices,
        "current_team": 1,
        "scores": {1: 0, 2: 0},
        "submitted": False,
        "answers": [],
        "selected_reference": None,
        "results": [],
        "placements": {},
        "shuffled_bank": initial_shuffled,
    }


def _tokenize(text):
    return re.findall(r"\b[\w']+\b|[^\w\s]", text)


def _render_verse(verse, answer_values=None, submitted=False, shuffled_bank=None, selected_reference=None):
    answer_values = answer_values or [""] * len(verse["blanks"])
    blank_map = {word.lower(): index for index, word in enumerate(verse["blanks"])}
    seen = set()
    tokens = []

    placed_words = set(w for w in answer_values if w)

    for token in _tokenize(verse["text"]):
        token_lower = token.lower()
        if token_lower in blank_map and token_lower not in seen:
            idx = blank_map[token_lower]
            seen.add(token_lower)
            current_word = answer_values[idx] if len(answer_values) > idx else ""
            is_draggable = "true" if (current_word and not submitted) else "false"

            tokens.append(
                html.Div(
                    current_word if current_word else "_____",
                    id={"type": f"{PREFIX}-slot", "index": idx},
                    className="dm-slot",
                    draggable=is_draggable,
                    **{"data-index": str(idx), "data-word": current_word},
                    style={
                        "display": "inline-flex",
                        "alignItems": "center",
                        "justifyContent": "center",
                        "minWidth": "120px",
                        "padding": "0.35rem 0.7rem",
                        "margin": "0 0.2rem",
                        "borderRadius": "8px",
                        "border": "2px dashed #0F172A" if not current_word else "2px solid #4F46E5",
                        "backgroundColor": "#EEF2FF" if current_word else "#FFFFFF",
                        "color": "#1E1B4B" if current_word else "#94A3B8",
                        "fontWeight": "bold",
                        "minHeight": "42px",
                        "verticalAlign": "middle",
                        "cursor": "grab" if (current_word and not submitted) else "default",
                    },
                )
            )
        else:
            tokens.append(html.Span(token, style={"whiteSpace": "pre-wrap"}))

        if token and token[-1].isalnum():
            tokens.append(html.Span(" ", style={"whiteSpace": "pre-wrap"}))

    if not shuffled_bank:
        shuffled_bank = list(verse["blanks"])
        random.shuffle(shuffled_bank)

    word_bank = []
    for idx, word in enumerate(shuffled_bank):
        is_placed = word in placed_words
        word_bank.append(
            html.Div(
                word,
                key=f"bank-{idx}",
                id={"type": f"{PREFIX}-word", "index": idx, "word": word},
                className="dm-word",
                draggable="false" if (is_placed or submitted) else "true",
                **{"data-index": str(idx), "data-word": word},
                style={
                    "padding": "0.6rem 0.9rem",
                    "borderRadius": "8px",
                    "backgroundColor": "#F1F5F9" if is_placed else "#E0E7FF",
                    "border": "1px solid #CBD5E1" if is_placed else "1px solid #818CF8",
                    "color": "#94A3B8" if is_placed else "#1E1B4B",
                    "fontWeight": "bold",
                    "cursor": "not-allowed" if (is_placed or submitted) else "grab",
                    "userSelect": "none",
                    "textAlign": "center",
                    "boxShadow": "none" if is_placed else "0 2px 8px rgba(79,70,229,0.15)",
                    "visibility": "hidden" if is_placed else "visible",
                },
            )
        )

    return html.Div(
        [
            # Scripture Reference Dropdown
            html.Div(
                [
                    html.Label(
                        "📌 Identify the Scripture Reference:",
                        style={"fontWeight": "bold", "fontSize": "1.1rem", "marginBottom": "0.5rem", "display": "block"},
                    ),
                    dcc.Dropdown(
                        id=f"{PREFIX}-ref-dropdown",
                        options=[{"label": ref, "value": ref} for ref in ALL_REFERENCES],
                        value=selected_reference,
                        placeholder="-- Select Scripture Reference --",
                        disabled=submitted,
                        style={"maxWidth": "400px", "marginBottom": "1rem"},
                    ),
                ],
                style={"backgroundColor": "#F1F5F9", "padding": "1rem", "borderRadius": "10px", "marginBottom": "1.2rem"},
            ),
            # Verse & Word Bank Section
            html.Div(
                [
                    html.Div(
                        tokens,
                        style={
                            "fontSize": "1.3rem",
                            "lineHeight": "2.1",
                            "padding": "1.25rem",
                            "backgroundColor": "#F8FAFC",
                            "border": "1px solid #CBD5E1",
                            "borderRadius": "12px",
                            "whiteSpace": "normal",
                            "flex": "1",
                        },
                    ),
                    html.Div(
                        [
                            html.Div("Word bank (10 words)", style={"fontWeight": "bold", "marginBottom": "0.7rem"}),
                            html.Div(
                                word_bank,
                                id=f"{PREFIX}-word-bank",
                                style={
                                    "display": "grid",
                                    "gridTemplateColumns": "repeat(auto-fit, minmax(120px, 1fr))",
                                    "gap": "0.6rem",
                                    "padding": "0.75rem",
                                    "backgroundColor": "#EEF2FF",
                                    "borderRadius": "10px",
                                    "border": "1px solid #C7D2FE",
                                    "minHeight": "100px",
                                },
                            ),
                        ],
                        style={"minWidth": "220px", "maxWidth": "260px", "marginLeft": "1rem"},
                    ),
                ],
                style={"display": "flex", "alignItems": "flex-start", "gap": "1rem"},
            ),
        ]
    )


def _render_game(state):
    if not state or not state.get("initialized"):
        return html.Div("Starting game…")

    if state["index"] >= len(VERSES):
        t1_score = state["scores"].get("1", state["scores"].get(1, 0))
        t2_score = state["scores"].get("2", state["scores"].get(2, 0))

        if t1_score > t2_score:
            winner = "🏆 Team 1 Wins!"
        elif t2_score > t1_score:
            winner = "🏆 Team 2 Wins!"
        else:
            winner = "🤝 It's a Tie!"

        return html.Div(
            [
                html.H2("🎉 Practice Complete!"),
                html.H3(winner, style={"color": "#2563EB", "margin": "1rem 0"}),
                html.Div(
                    [
                        html.Div(f"🔵 Team 1 Final Score: {t1_score}", style={"fontSize": "1.2rem"}),
                        html.Div(f"🔴 Team 2 Final Score: {t2_score}", style={"fontSize": "1.2rem"}),
                    ],
                    style={"marginBottom": "1.5rem", "display": "flex", "gap": "2rem"},
                ),
                html.Button("🔁 Start Again", id=f"{PREFIX}-restart", style={"padding": "0.75rem 1rem"}),
            ],
            style={"padding": "1rem", "maxWidth": "900px"},
        )

    current_verse_idx = state["verse_order"][state["index"]]
    verse = VERSES[current_verse_idx]

    answer_values = state.get("answers", [""] * len(verse["blanks"]))
    correct_answers = [word for word in verse["blanks"]]
    current_team = state.get("current_team", 1)

    t1_score = state["scores"].get("1", state["scores"].get(1, 0))
    t2_score = state["scores"].get("2", state["scores"].get(2, 0))

    team_color = "#2563EB" if current_team == 1 else "#DC2626"

    content = [
        html.Div(
            [
                html.H3("Doctrinal Mastery Match & Fill-In", style={"margin": "0"}),
                html.Div(
                    [
                        html.Span(
                            f"🔵 Team 1: {t1_score}",
                            style={
                                "fontWeight": "bold" if current_team == 1 else "normal",
                                "color": "#2563EB",
                                "padding": "0.4rem 0.8rem",
                                "borderRadius": "6px",
                                "backgroundColor": "#DBEAFE" if current_team == 1 else "transparent",
                            },
                        ),
                        html.Span(
                            f"🔴 Team 2: {t2_score}",
                            style={
                                "fontWeight": "bold" if current_team == 2 else "normal",
                                "color": "#DC2626",
                                "padding": "0.4rem 0.8rem",
                                "borderRadius": "6px",
                                "backgroundColor": "#FEE2E2" if current_team == 2 else "transparent",
                            },
                        ),
                    ],
                    style={"display": "flex", "gap": "1rem", "alignItems": "center"},
                ),
            ],
            style={
                "display": "flex",
                "justifyContent": "space-between",
                "alignItems": "center",
                "marginBottom": "1rem",
            },
        ),
        html.Div(
            f"Round {state['index'] + 1} of {len(VERSES)} • CURRENT TURN: TEAM {current_team}",
            style={"marginBottom": "1rem", "fontWeight": "bold", "color": team_color, "fontSize": "1.1rem"},
        ),
        _render_verse(verse, answer_values, state.get("submitted", False), state.get("shuffled_bank"), state.get("selected_reference")),
    ]

    if state.get("submitted"):
        correct_words = sum(
            1 for value, expected in zip(answer_values, correct_answers) if value.strip().lower() == expected.lower()
        )
        is_ref_correct = state.get("selected_reference") == verse["reference"]
        ref_points = 5 if is_ref_correct else 0
        total_round_pts = correct_words + ref_points
        next_team = 2 if current_team == 1 else 1

        correct_ref_text = verse["reference"]
        ref_status_msg = "✅ Correct (+5 pts)" if is_ref_correct else f"❌ Incorrect (Correct was: {correct_ref_text})"

        content.extend(
            [
                html.Div(
                    [
                        html.Div(f"Team {current_team} scored {total_round_pts} points this round!"),
                        html.Div(f"• Words: {correct_words}/10 correct ({correct_words} pts)"),
                        html.Div(f"• Reference: {ref_status_msg}"),
                    ],
                    style={
                        "marginTop": "1rem",
                        "padding": "0.8rem 1rem",
                        "backgroundColor": "#DBEAFE" if current_team == 1 else "#FEE2E2",
                        "borderRadius": "8px",
                        "fontWeight": "bold",
                        "color": team_color,
                    },
                ),
                html.Div(
                    [
                        html.Strong("Answer key: "),
                        ", ".join(correct_answers),
                    ],
                    style={"marginTop": "0.8rem", "fontSize": "1rem"},
                ),
                html.Button(
                    f"➡️ Next Verse (Pass to Team {next_team})",
                    id=f"{PREFIX}-next",
                    style={"marginTop": "1rem", "padding": "0.75rem 1rem"},
                ),
            ]
        )
    else:
        content.append(
            html.Button(
                f"✅ Submit Answers for Team {current_team}",
                id=f"{PREFIX}-submit",
                style={"marginTop": "1rem", "padding": "0.75rem 1rem"},
            )
        )

    return html.Div(content, style={"maxWidth": "1000px", "padding": "1rem"})


def layout():
    return html.Div(
        [
            dcc.Store(id=f"{PREFIX}-state", storage_type="session", data={}),
            dcc.Store(id=f"{PREFIX}-drag-state", storage_type="memory", data={}),
            html.Div(
                [
                    html.H2("📖 Doctrinal Mastery 2-Team Challenge"),
                    html.P("Identify the scripture reference from the list of 24, then drag the 10 missing words into place!"),
                    html.Button("▶ Start 2-Team Game", id=f"{PREFIX}-start", style={"padding": "0.75rem 1rem", "marginBottom": "1rem"}),
                    html.Div(id=f"{PREFIX}-body"),
                ],
                style={"maxWidth": "1100px", "margin": "0 auto", "padding": "1.5rem"},
            ),
        ]
    )


def register_callbacks(app):
    app.clientside_callback(
        """
        function(children) {
            setTimeout(function() {
                var words = document.querySelectorAll('.dm-word[draggable="true"]');
                var slots = document.querySelectorAll('.dm-slot');
                var bank = document.getElementById('dm-word-bank');

                var draggedWord = null;
                var sourceSlotIndex = null;

                function handleDragStart(e) {
                    draggedWord = e.target.getAttribute('data-word');
                    sourceSlotIndex = e.target.getAttribute('data-index');
                    e.dataTransfer.setData('text/plain', draggedWord);
                    e.target.style.opacity = '0.5';
                }

                function handleDragEnd(e) {
                    e.target.style.opacity = '1.0';
                }

                words.forEach(function(word) {
                    word.removeEventListener('dragstart', handleDragStart);
                    word.removeEventListener('dragend', handleDragEnd);
                    word.addEventListener('dragstart', handleDragStart);
                    word.addEventListener('dragend', handleDragEnd);
                });

                slots.forEach(function(slot) {
                    slot.removeEventListener('dragstart', handleDragStart);
                    slot.removeEventListener('dragend', handleDragEnd);
                    
                    if (slot.getAttribute('draggable') === 'true') {
                        slot.addEventListener('dragstart', handleDragStart);
                        slot.addEventListener('dragend', handleDragEnd);
                    }

                    slot.addEventListener('dragover', function(e) {
                        e.preventDefault();
                        slot.style.border = '2px dashed #4F46E5';
                    });

                    slot.addEventListener('dragleave', function(e) {
                        slot.style.border = slot.getAttribute('data-word') ? '2px solid #4F46E5' : '2px dashed #0F172A';
                    });

                    slot.addEventListener('drop', function(e) {
                        e.preventDefault();
                        var targetIndex = slot.getAttribute('data-index');
                        
                        var dragStore = dash_clientside.set_props ? 
                            JSON.parse(sessionStorage.getItem('dm-drag-state') || '{}') : {};

                        if (sourceSlotIndex !== null && sourceSlotIndex !== undefined) {
                            delete dragStore[sourceSlotIndex];
                        }

                        dragStore[targetIndex] = draggedWord;

                        var storeEl = document.getElementById('dm-drag-state');
                        if (storeEl) {
                            dash_clientside.set_props('dm-drag-state', {data: dragStore});
                        }
                    });
                });

                if (bank) {
                    bank.addEventListener('dragover', function(e) { e.preventDefault(); });
                    bank.addEventListener('drop', function(e) {
                        e.preventDefault();
                        if (sourceSlotIndex !== null && sourceSlotIndex !== undefined) {
                            var dragStore = JSON.parse(sessionStorage.getItem('dm-drag-state') || '{}');
                            delete dragStore[sourceSlotIndex];
                            dash_clientside.set_props('dm-drag-state', {data: dragStore});
                        }
                    });
                }
            }, 100);
            return window.dash_clientside.no_update;
        }
        """,
        Output(f"{PREFIX}-drag-state", "id"),
        Input(f"{PREFIX}-body", "children"),
        prevent_initial_call=True,
    )

    @app.callback(
        Output(f"{PREFIX}-state", "data"),
        Output(f"{PREFIX}-body", "children"),
        Input(f"{PREFIX}-start", "n_clicks"),
        Input(f"{PREFIX}-submit", "n_clicks", allow_optional=True),
        Input(f"{PREFIX}-next", "n_clicks", allow_optional=True),
        Input(f"{PREFIX}-restart", "n_clicks", allow_optional=True),
        Input(f"{PREFIX}-drag-state", "data", allow_optional=True),
        Input(f"{PREFIX}-ref-dropdown", "value", allow_optional=True),
        State(f"{PREFIX}-state", "data"),
        State({"type": f"{PREFIX}-word", "index": ALL, "word": ALL}, "children"),
    )
    def update_game(_start_clicks, _submit_clicks, _next_clicks, _restart_clicks, drag_state, ref_selected, state, _word_children):
        trigger = ctx.triggered_id

        if not state or not state.get("initialized"):
            state = _new_game_state()

        if trigger in (None, f"{PREFIX}-start", f"{PREFIX}-restart"):
            if trigger in (f"{PREFIX}-start", f"{PREFIX}-restart"):
                state = _new_game_state()
        elif trigger == f"{PREFIX}-ref-dropdown":
            state["selected_reference"] = ref_selected
        elif trigger == f"{PREFIX}-drag-state":
            placements = drag_state or {}
            state["placements"] = placements
            current_verse_idx = state["verse_order"][state["index"]]
            verse = VERSES[current_verse_idx]
            state["answers"] = [placements.get(str(i), "") for i in range(len(verse["blanks"]))]
        elif trigger == f"{PREFIX}-submit":
            current_verse_idx = state["verse_order"][state["index"]]
            verse = VERSES[current_verse_idx]

            state["answers"] = [state.get("placements", {}).get(str(i), "") for i in range(len(verse["blanks"]))]
            state["submitted"] = True

            correct_words = sum(
                1
                for value, expected in zip(state["answers"], verse["blanks"])
                if (value or "").strip().lower() == expected.lower()
            )
            is_ref_correct = state.get("selected_reference") == verse["reference"]
            round_score = correct_words + (5 if is_ref_correct else 0)

            current_team = str(state.get("current_team", 1))
            state["scores"][current_team] = state["scores"].get(current_team, 0) + round_score
            state["results"].append(
                {
                    "team": current_team,
                    "reference": verse["reference"],
                    "selected_ref": state.get("selected_reference"),
                    "word_score": correct_words,
                    "ref_score": 5 if is_ref_correct else 0,
                    "total": len(verse["blanks"]) + 5,
                }
            )
        elif trigger == f"{PREFIX}-next":
            if state.get("submitted"):
                state["index"] += 1
                state["current_team"] = 2 if state.get("current_team", 1) == 1 else 1
                state["submitted"] = False
                state["answers"] = []
                state["placements"] = {}
                state["selected_reference"] = None

                if state["index"] < len(VERSES):
                    next_verse_idx = state["verse_order"][state["index"]]
                    next_shuffled = list(VERSES[next_verse_idx]["blanks"])
                    random.shuffle(next_shuffled)
                    state["shuffled_bank"] = next_shuffled

        return state, _render_game(state)
