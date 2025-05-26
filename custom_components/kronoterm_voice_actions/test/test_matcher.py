# src/kronoterm_voice_actions/test/test_matcher.py

from kronoterm_voice_actions.wyoming import matcher
import pytest

# Manually extracted commands from mqtt_client.py
commands = [
    "ali je sistem vklopljen", "ali je sistem izklopljen", "kakšno je stanje sistema",
    "kakšna funkcija se izvaja", "kakšna funkcija delovanja se izvaja", "ali je rezervni vir vklopljen",
    "ali je rezervni vir izklopljen", "kakšen je status rezervnega vira", "ali je alternativni vir vklopljen",
    "ali je alternativni vir izklopljen", "kakšen je status alternativnega vira", "kakšen je trenuten režim delovanja",
    "kakšen je režim delovanja", "kakšen je trenuten program", "kakšen je program delovanja",
    "kakšen je status hitrega segrevanja sanitarne vode", "ali je hitro segrevanje sanitarne vode vklopljeno",
    "ali je hitro segrevanje sanitarne vode izklopljeno", "kakšen je status odtaljevanja",
    "ali je odtaljevanje vklopljeno", "ali je odtaljevanje izklopljeno", "ali se odtaljevanje izvaja",
    "vklopi sistem", "vklopi toplotno črpalko in ogrevalne kroge", "izklopi sistem",
    "izklopi toplotno črpalko in ogrevalne kroge", "nastavi normalen režim", "nastavi režim na normalen način",
    "vklopi normalen režim", "nastavi eco režim", "nastavi režim na eco način", "vklopi eco režim",
    "nastavi com režim", "nastavi režim na com način", "vklopi com režim", "vklopi hitro segrevanje sanitarne vode",
    "izklopi hitro segrevanje sanitarne vode", "kakšna je trenutna obremenitev toplotne črpalke",
    "nastavi želeno temperaturo sanitarne vode na <temperature> stopinj",
    "nastavi temperaturo sanitarne vode na <temperature> stopinj", "segrej sanitarno vodo na <temperature> stopinj",
    "kakšna je trenutna želena temperatura sanitarne vode", "izklopi segrevanje sanitarne vode",
    "nastavi normalen režim sanitarne vode", "nastavi režim sanitarne vode na normalno",
    "vklopi normalen režim segrevanja sanitarne vode", "nastavi režim sanitarne vode po urniku",
    "vklopi režim segrevanja sanitarne vode po urniku", "kakšen je trenuten način delovanja sanitarne vode po urniku",
    "kakšna je temperatura sanitarne vode", "nastavi temperaturo prostora ena na <temperature> stopinj",
    "nastavi želeno temperaturo prostora prvega kroga na <temperature> stopinj",
    "kakšna je trenutna želena temperatura prostora prvega kroga", "kakšna je trenutna želena temperatura prostora ena",
    "izklopi prvi ogrevalni krog", "izklopi ogrevalni krog ena",
    "nastavi delovanje prvega ogrevalnega kroga na normalni režim",
    "nastavi delovanje ogrevalnega kroga ena na normalni režim", "vklopi normalni režim na ogrevalnem krogu ena",
    "vklopi normalni režim na prvem ogrevalnem krogu",
    "nastavi delovanje prvega ogrevalnega kroga na delovanje po urniku",
    "nastavi delovanje ogrevalnega kroga ena na delovanje po urniku",
    "vklopi delovanje po urniku na ogrevalnem krogu ena", "vklopi delovanje po urniku na prvem ogrevalnem krogu",
    "kakšen je status delovanja prvega ogrevalnega kroga", "kakšen je status delovanja ogrevalnega kroga ena",
    "kakšna je temperatura ogrevalnega kroga ena", "kakšna je temperatura prvega ogrevalnega kroga",
    "nastavi temperaturo prostora dva na <temperature> stopinj",
    "nastavi želeno temperaturo prostora drugega kroga na <temperature> stopinj",
    "kakšna je trenutna želena temperatura prostora drugega kroga",
    "kakšna je trenutna želena temperatura prostora dva", "izklopi drugi ogrevalni krog",
    "izklopi ogrevalni krog dva", "nastavi delovanje drugega ogrevalnega kroga na normalni režim",
    "nastavi delovanje ogrevalnega kroga dva na normalni režim", "vklopi normalni režim na ogrevalnem krogu dva",
    "vklopi normalni režim na drugem ogrevalnem krogu",
    "nastavi delovanje drugega ogrevalnega kroga na delovanje po urniku",
    "nastavi delovanje ogrevalnega kroga dva na delovanje po urniku",
    "vklopi delovanje po urniku na ogrevalnem krogu dva", "vklopi delovanje po urniku na drugem ogrevalnem krogu",
    "kakšen je status delovanja drugega ogrevalnega kroga", "kakšen je status delovanja ogrevalnega kroga dva",
    "kakšna je temperatura ogrevalnega kroga dva", "kakšna je temperatura drugega ogrevalnega kroga",
    "nastavi temperaturo prostora tri na <temperature> stopinj",
    "nastavi želeno temperaturo prostora tretjega kroga na <temperature> stopinj",
    "kakšna je trenutna želena temperatura prostora tretjega kroga",
    "kakšna je trenutna želena temperatura prostora tri", "izklopi tretji ogrevalni krog",
    "izklopi ogrevalni krog tri", "nastavi delovanje tretjega ogrevalnega kroga na normalni režim",
    "nastavi delovanje ogrevalnega kroga tri na normalni režim", "vklopi normalni režim na ogrevalnem krogu tri",
    "vklopi normalni režim na tretjem ogrevalnem krogu",
    "nastavi delovanje tretjega ogrevalnega kroga na delovanje po urniku",
    "nastavi delovanje ogrevalnega kroga tri na delovanje po urniku",
    "vklopi delovanje po urniku na ogrevalnem krogu tri", "vklopi delovanje po urniku na tretjem ogrevalnem krogu",
    "kakšen je status delovanja tretjega ogrevalnega kroga", "kakšen je status delovanja ogrevalnega kroga tri",
    "kakšna je temperatura ogrevalnega kroga tri", "kakšna je temperatura tretjega ogrevalnega kroga",
    "nastavi temperaturo prostora štiri na <temperature> stopinj",
    "nastavi želeno temperaturo prostora četrtega kroga na <temperature> stopinj",
    "kakšna je trenutna želena temperatura prostora četrtega kroga",
    "kakšna je trenutna želena temperatura prostora štiri", "izklopi četrti ogrevalni krog",
    "izklopi ogrevalni krog štiri", "nastavi delovanje četrtega ogrevalnega kroga na normalni režim",
    "nastavi delovanje ogrevalnega kroga štiri na normalni režim",
    "vklopi normalni režim na ogrevalnem krogu štiri", "vklopi normalni režim na četrtem ogrevalnem krogu",
    "nastavi delovanje četrtega ogrevalnega kroga na delovanje po urniku",
    "nastavi delovanje ogrevalnega kroga štiri na delovanje po urniku",
    "vklopi delovanje po urniku na ogrevalnem krogu štiri",
    "vklopi delovanje po urniku na četrtem ogrevalnem krogu", "kakšen je status delovanja četrtega ogrevalnega kroga",
    "kakšen je status delovanja ogrevalnega kroga štiri", "kakšna je temperatura ogrevalnega kroga štiri",
    "kakšna je temperatura četrtega ogrevalnega kroga"
]

# Test slovenian_word_to_number_strict
def test_parse_slovene_number_strict_basic():
    assert (matcher.slovenian_word_to_number_strict("ena")) == '1.0'
    assert (matcher.slovenian_word_to_number_strict("dvanajst")) == '12.0'
    assert (matcher.slovenian_word_to_number_strict("dvajset")) == '20.0'
    assert (matcher.slovenian_word_to_number_strict("petindvajset")) == '25.0'
    assert (matcher.slovenian_word_to_number_strict("25")) == '25.0'
    assert (matcher.slovenian_word_to_number_strict("25.5")) == '25.5'
    assert (matcher.slovenian_word_to_number_strict("nič")) == '0.0'
    assert matcher.slovenian_word_to_number_strict("mačipiču") is None

# Test slovenian_word_to_number (with typos)
def test_parse_slovene_number_typos():
    assert (matcher.slovenian_word_to_number("dvaset")) == '20.0'
    assert (matcher.slovenian_word_to_number("šestnajst")) == '16.0'
    assert (matcher.slovenian_word_to_number("trinajst")) == '13.0'

# Test replace_numbers_with_digits
def test_replace_numbers():
    assert matcher.replace_numbers_with_digits("nastavi temperaturo na dvajset stopinj") == "nastavi temperaturo na 20.0 stopinj"
    assert matcher.replace_numbers_with_digits("nastavi na pet in dvajset stopinj") == "nastavi na 25.0 stopinj"
    assert matcher.replace_numbers_with_digits("ena dva tri") == "1.0 2.0 3.0"
    assert matcher.replace_numbers_with_digits("dve celih pet") == "2.5"

# Test includes_temperature
def test_includes_temperature():
    assert matcher.includes_temperature("nastavi temperaturo na 20 stopinj") == True
    assert matcher.includes_temperature("kakšna je temperatura?") == False
    assert matcher.includes_temperature("segrej vodo na 50°C") == True
    assert matcher.includes_temperature("koliko je stopinj zunaj") == False

# Test match_command with perfect sentences
def test_match_command_perfect():
    action, param = matcher.match_command("kakšna je temperatura sanitarne vode", commands)
    assert action == "kakšna je temperatura sanitarne vode"
    assert param is None

    action, param = matcher.match_command("nastavi temperaturo prostora ena na 22 stopinj", commands)
    assert action in [
        "nastavi temperaturo prostora ena na <temperature> stopinj",
        "nastavi želeno temperaturo prostora prvega kroga na <temperature> stopinj"
    ]
    assert param == 22.0

    action, param = matcher.match_command("vklopi sistem", commands)
    assert action == "vklopi sistem"
    assert param is None

# Test match_command with botched sentences
def test_match_command_botched():
    action, param = matcher.match_command("kšna je tempertura sanitarne oude", commands)
    assert action == "kakšna je temperatura sanitarne vode"
    assert param is None

    action, param = matcher.match_command("prosim vklopi sistem zdaj", commands)
    assert action == "vklopi sistem"
    assert param is None

    action, param = matcher.match_command("nastavi temeraturo prostora ena na dvaindvajset stopinj", commands)
    assert action in [
        "nastavi temperaturo prostora ena na <temperature> stopinj",
        "nastavi želeno temperaturo prostora prvega kroga na <temperature> stopinj"
    ]
    assert param == 22.0

    with pytest.raises(ValueError):
         matcher.match_command("vrabec na strehi in kamen v roki", commands)

    action, param = matcher.match_command("prosim te nastavi mi temperturo za sanitarno vodo na 45 stopinj", commands)
    assert action in [
        "nastavi želeno temperaturo sanitarne vode na <temperature> stopinj",
        "nastavi temperaturo sanitarne vode na <temperature> stopinj",
        "segrej sanitarno vodo na <temperature> stopinj"
    ]
    assert param == 45.0

    action, param = matcher.match_command("nastavi temperaturo prostora dva na endvajst celih pet stopinj", commands)
    assert action in [
        "nastavi temperaturo prostora dva na <temperature> stopinj",
        "nastavi želeno temperaturo drugega prvega kroga na <temperature> stopinj"
    ]
    assert param == 21.5

    action, param = matcher.match_command("nastavi temperaturo prostora dva na 21.5 stopinj", commands)
    assert action in [
        "nastavi temperaturo prostora dva na <temperature> stopinj",
        "nastavi želeno temperaturo drugega prvega kroga na <temperature> stopinj"
    ]
    assert param == 21.5

    action, param = matcher.match_command("uklopi sstm", commands)
    assert action == "vklopi sistem"
    assert param is None