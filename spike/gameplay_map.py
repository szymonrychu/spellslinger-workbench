"""Hand-mapped actions and expected outcomes for MCM gameplay scenarios (T-57 spike).

`translate.py` extracts each scenario's board (hand, battlefield, library, graveyard per
player) from the MCM `Scenario()` builder by AST; this table supplies what the MCM test
does with it and what it asserts, written in ironsmith's XMage-port operation language
(`scripts/mage-port-runner.mjs`). Player 0 is alice (the starting player), player 1 bob.

`partial` names the MCM assertions that have no operation in that language and so are not
compared. Everything in UNTRANSLATABLE is skipped with the reason given.
"""

from __future__ import annotations

MAIN = {"turn": 1, "phase": "PRECOMBAT_MAIN"}
STOP = [{"op": "setStopAt", "turn": 1, "phase": "BEGIN_COMBAT"}, {"op": "execute"}]


def cast(name: str, player: int = 0, **extra: object) -> dict:
    return {"op": "castSpell", **MAIN, "player": player, "name": name, **extra}


def activate(ability: str, player: int = 0, **extra: object) -> dict:
    return {"op": "activateAbility", **MAIN, "player": player, "ability": ability, **extra}


def choice(value: object, player: int = 0) -> dict:
    return {"op": "setChoice", "player": player, "value": value}


def permanents(name: str, count: int, player: int = 0) -> dict:
    return {"op": "assertPermanentCount", "player": player, "name": name, "count": count}


def exiled(name: str, count: int) -> dict:
    return {"op": "assertExileCount", "name": name, "count": count}


IMPRINT_CHANT = [
    cast("Isochron Scepter"),
    choice(True),
    choice("Orim's Chant"),
]

PITCH_RIDER = [
    cast("Allosaurus Rider"),
    choice("Veil of Summer"),
    choice("Nature's Claim"),
]

GAMEPLAY: dict[str, dict] = {
    "test_belcher_deck::test_every_land_back_face_taps_for_mana": {
        "partial": "only the land play is compared; the parse_abilities sweep is MCM-internal",
        "ops": [
            {"op": "playLand", **MAIN, "player": 0, "name": "Jwari Ruins"},
            *STOP,
            permanents("Jwari Ruins", 1),
        ],
    },
    "test_belcher_deck::test_charbelcher_deals_damage_when_it_reveals_a_pile_of_nonlands": {
        "ops": [
            activate("{3}, {T}", target="playerB"),
            *STOP,
            {"op": "assertLife", "player": 1, "life": 16},
        ],
    },
    "test_esper_control_deck::test_the_cage_refuses_a_flashback_granted_cast_out_of_the_graveyard": {  # noqa: E501
        "ops": [
            cast("Flashback", target="Lightning Bolt"),
            {
                "op": "assertPlayableAbility",
                **MAIN,
                "player": 0,
                "label": "Cast Lightning Bolt",
                "expected": False,
            },
            {"op": "assertGraveyardCount", "player": 0, "name": "Lightning Bolt", "count": 1},
        ],
    },
    "test_esper_control_deck::test_the_cage_lets_a_creature_spell_from_the_hand_through": {
        "ops": [cast("Grizzly Bears"), *STOP, permanents("Grizzly Bears", 1)],
    },
    "test_izzet_prowess_deck::test_a_bolt_from_this_list_pumps_a_swiftspear_from_this_list": {
        "ops": [
            cast("Lightning Bolt", target="playerB"),
            *STOP,
            {
                "op": "assertPowerToughness",
                "player": 0,
                "name": "Monastery Swiftspear",
                "power": 2,
                "toughness": 3,
            },
        ],
    },
    "test_scepter_chant_deck::test_isochron_scepter_imprints_orims_chant_on_entry": {
        "partial": "card_imprinted_on (the imprint link itself) is MCM-internal; zones compared",
        "ops": [
            *IMPRINT_CHANT,
            *STOP,
            permanents("Isochron Scepter", 1),
            exiled("Orim's Chant", 1),
        ],
    },
    "test_scepter_chant_deck::test_the_imprinted_card_itself_never_leaves_exile": {
        "partial": "card_imprinted_on is MCM-internal; the Chant staying in exile is compared",
        "ops": [
            *IMPRINT_CHANT,
            activate("{2}, {T}:"),
            choice(True),
            {"op": "addTarget", "player": 0, "target": "playerB"},
            *STOP,
            exiled("Orim's Chant", 1),
        ],
    },
    "test_scepter_chant_deck::test_declining_the_copy_leaves_nothing_behind": {
        "ops": [
            *IMPRINT_CHANT,
            activate("{2}, {T}:"),
            choice(False),
            *STOP,
            {"op": "assertStackSize", "count": 0},
            exiled("Orim's Chant", 1),
        ],
    },
    "test_storm_deck::test_storm_copies_the_spell_once_per_spell_cast_before_it": {
        "partial": "the transient stack contents and spells_cast_this_turn are not compared; "
        "the resulting three dragons are",
        "ops": [
            cast("Pyretic Ritual"),
            cast("Pyretic Ritual"),
            cast("Stormscale Scion"),
            *STOP,
            permanents("Stormscale Scion", 3),
        ],
    },
    "test_allosaurus_combo_deck::test_allosaurus_rider_is_pitch_cast_for_two_green_cards": {
        "partial": "the alternative-cost description text and untapped-land count are not compared",
        "ops": [
            *PITCH_RIDER,
            *STOP,
            permanents("Allosaurus Rider", 1),
            exiled("Veil of Summer", 1),
            exiled("Nature's Claim", 1),
            {
                "op": "assertPowerToughness",
                "player": 0,
                "name": "Allosaurus Rider",
                "power": 3,
                "toughness": 3,
            },
        ],
    },
    "test_allosaurus_combo_deck::test_neoform_turns_the_pitched_rider_into_a_fatty": {
        "partial": "printed mana costs are not compared (card data, not rules)",
        "ops": [
            *PITCH_RIDER,
            cast("Neoform"),
            choice("Allosaurus Rider"),
            choice("Griselbrand"),
            *STOP,
            {"op": "assertGraveyardCount", "player": 0, "name": "Allosaurus Rider", "count": 1},
            permanents("Griselbrand", 1),
            {
                "op": "assertCounterCount",
                "player": 0,
                "name": "Griselbrand",
                "counter": "P1P1",
                "count": 1,
            },
        ],
    },
    "test_allosaurus_combo_deck::test_summoners_pact_fetches_the_rider_and_bills_the_next_upkeep": {  # noqa: E501
        "partial": "only the search is compared; the next-upkeep loss needs a game-over "
        "assertion the operation language lacks",
        "ops": [
            cast("Summoner's Pact"),
            choice("Allosaurus Rider"),
            *STOP,
            {"op": "assertHandCount", "player": 0, "name": "Allosaurus Rider", "count": 1},
            {"op": "assertGraveyardCount", "player": 0, "name": "Summoner's Pact", "count": 1},
        ],
    },
    "test_deck_45c_aggro::test_a_land_from_this_deck_can_be_played_as_a_special_action": {
        "ops": [
            {"op": "playLand", **MAIN, "player": 0, "name": "Mountain"},
            *STOP,
            permanents("Mountain", 1),
            {"op": "assertStackSize", "count": 0},
        ],
    },
    "test_deck_45c_aggro::test_leyline_of_the_guildpact_makes_every_land_every_basic_land_type": {
        "ops": [
            *STOP,
            *[
                {"op": "assertSubtype", "name": "Mountain", "subtype": subtype}
                for subtype in ("Plains", "Island", "Swamp", "Mountain", "Forest")
            ],
        ],
    },
    "test_deck_45c_aggro::test_territorial_kavu_has_power_equal_to_its_domain": {
        "ops": [
            *STOP,
            {
                "op": "assertPowerToughness",
                "player": 0,
                "name": "Territorial Kavu",
                "power": 3,
                "toughness": 3,
            },
        ],
    },
}

UNTRANSLATABLE: dict[str, str] = {
    "test_esper_control_deck::test_the_cage_keeps_a_creature_card_in_the_graveyard_it_came_from": (  # noqa: E501
        "calls the engine directly (game.put_onto_battlefield) with no player action to replay"
    ),
    "test_grinding_cam_deck::test_mox_amber_adds_nothing_without_a_legendary_creature_or_planeswalker": (  # noqa: E501
        "asserts MCM's refusal (ValueError) to activate; the operation language has no "
        "mana-pool assertion to check that nothing was added"
    ),
    "test_storm_deck::test_a_ritual_nets_mana_into_the_pool": (
        "asserts the floating mana pool; the operation language has no mana-pool assertion"
    ),
    "test_storm_deck::test_ruby_medallion_discounts_a_red_spell": (
        "reads MCM's Casting.total_cost API rather than playing the spell"
    ),
    "test_scepter_chant_deck::test_the_scepter_recasts_the_imprinted_chant": (
        "asserts a transient stack state (the copy waiting on the stack); the runner settles "
        "the stack before assertions"
    ),
    "test_scepter_chant_deck::test_the_copy_resolves_and_locks_the_opponent_out": (
        "asserts the copy object on the stack (is_copy, targets) before it resolves"
    ),
    "test_deck_45c_aggro::test_each_land_adds_every_colour_it_prints": (
        "probes MCM's mana_from helper on a land without a game action"
    ),
    "test_deck_45c_aggro::test_a_fetchland_makes_no_mana_at_all": (
        "probes MCM's mana_from helper on a land without a game action"
    ),
    "test_deck_45c_aggro::test_the_manabase_covers_all_five_colours_between_them": (
        "probes MCM's mana_from helper on lands without a game action"
    ),
    "test_hollow_one_deck::test_hollow_one_is_cheaper_after_a_discard": (
        "reads MCM's game.cost_reduction_for API after a direct discard_cards call"
    ),
    "test_broodscale_bloodchief_deck::test_gemstone_caverns_can_begin_the_game_on_the_battlefield": (  # noqa: E501
        "uses an MCM helper that rigs the opening hand; ironsmith's startMatch has no rigged "
        "opening hand"
    ),
    "test_broodscale_bloodchief_deck::test_devourer_of_destiny_can_be_revealed_from_the_opening_hand": (  # noqa: E501
        "uses an MCM helper that rigs the opening hand; ironsmith's startMatch has no rigged "
        "opening hand"
    ),
    "test_broodscale_bloodchief_deck::test_the_starting_player_is_never_offered_the_caverns": (
        "uses an MCM helper that rigs the opening hand"
    ),
}
