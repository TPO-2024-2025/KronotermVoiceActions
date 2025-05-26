# Kronoterm Voice Actions

## Predpogoji

* Delujoča namestitev **Home Assistant OS** ali **Home Assistant Supervised**. Ta dodatek **ne deluje** z metodo namestitve "Home Assistant Container", ker nima sistema za upravljanje dodatkov (Supervisor).
* Nameščen in delujoč **Whisper Add-on**, povezan z vašim Home Assistantom. Namestitev iz trgovine z dodatki (`Settings` > `Add-ons` > `Add-on Store`).
* Nameščen in delujoč **Piper Add-on** (neobvezno, vendar priporočljivo), povezan z vašim Home Assistantom. Namestitev iz trgovine z dodatki (`Settings` > `Add-ons` > `Add-on Store`).
* Naložena koda iz tega repozitorija.

## Ročna namestitev

Ta navodila opisujejo, kako namestiti Addon v vaš Home Assistant sistem.

### Namestitev dodatka

Za namestitev morate mapo `kronoterm_voice_actions/wyoming` skopirati v mapo `/config/custom_components/` znotraj vašega Home Assistant sistema. To najlažje storite preko SSH povezave.

#### 1. Namestitev SSH na Home Assistant

Ta metoda uporablja ukaz scp (Secure Copy) za prenos datotek preko SSH protokola.

Zato predlagamo Add-on `Advanced SSH & Web Terminal`. S pomočjo njihove dokumentacije si namestite SSH bodisi z geslom bodisi z kriptografskim ključem.

**NUJNO** morate nastaviti `sftp=true` in `username=root` v konfiguraciji tega Add-ona.

**Če imate omogočen standardni SSH dostop do sistema HAOS/Supervised:** Preskočite ta korak, vendar se prepričajte, da poznate uporabniško ime, geslo/ključ in IP naslov za povezavo.

#### 2. Kopiranje Add-ona v Home Assistant

Odprite terminal ali ukazno vrstico **na vašem računalniku** (kjer imate shranjeno mapo `kronoterm_voice_actions/wyoming`)

Kreiranje mape custom_components:
```bash
shh -m hmac-sha2-512-etm@openssh.com root@<HA_IP_NASLOV>
cd /config
cd /config
mkdir custom_components
```
Kopiranje integracije:
```bash
scp -o MACs=hmac-sha2-512-etm@openssh.com -r /pot/do/mape/kronoterm_voice_actions/wyoming root@<HA_IP_NASLOV>:/config/custom_components/
```

* *(Primer: `scp -o MACs=hmac-sha2-512-etm@openssh.com -r C:\Projekti\Projekt-16\custom_components\kronoterm_voice_actions/wyoming root@192.168.1.100:/config/custom_components/`)*
* *(Primer za Linux/macOS: `scp -o MACs=hmac-sha2-512-etm@openssh.com -r ~/Downloads/Projekt-16/custom_components/kronoterm_voice_actions/wyoming root@192.168.1.100:/config/custom_components/`)*
* *(Primer: `scp -o MACs=hmac-sha2-512-etm@openssh.com -r C:\Projekti\Projekt-16\custom_components\kronoterm_voice_actions/wyoming root@192.168.1.100:/config/custom_components/`)*
* *(Primer za Linux/macOS: `scp -o MACs=hmac-sha2-512-etm@openssh.com -r ~/Downloads/Projekt-16/custom_components/kronoterm_voice_actions/wyoming root@192.168.1.100:/config/custom_components/`)*

* Vpisati boste morali geslo za SSH (ali pa bo uporabljen vaš SSH ključ, če je tako nastavljeno).
* Parameter `-r` zagotovi, da se skopira celotna mapa z vsebino.
* Parameter `-o MACs=<hmac-sha2-512-etm@openssh.com>` poskrbi, da se povezava vzpostavi četudi pride do `Corrupted MAC` napake, kar se lahko zgodi.
* Kopiranje lahko, če se povežete na sistem s `ssh root@<HAOS_IP> -m hmac-sha2-512-etm@openssh.com`.

**Preverjanje (neobvezno):**
Lahko se povežete na Home Assistant preko SSH (`ssh vase_ssh_uporabnisko_ime@<HA_IP_NASLOV>`) in zaženete ukaz `ls /config/custom_components/`, da preverite, ali je mapa `kronoterm_voice_control` prisotna.

#### 3. Osvežitev Home Assistant

1. **Ponovno začenite Home Assistant**
    * Pojdite v `Settings` in v desnjem zgornjem kotu kliknite tri pikice. Nato izberite `Restart Home Assistant` in nato zopet isto.
2. **Osvežite Integracije:**
    * V vmesniku Home Assistant pojdite na `Settings` > `Devices & services`
    * Osvežite stran v brskalniku (npr. Ctrl+F5 v Windows/Linux, Cmd+Shift+R v macOS), da Home Assistant ponovno preveri lokalne dodatke.

---

## Namestitev preko HACS

1. **Dodajanje repository-a**
 V vmesniku Home Assistant odprite sistem HACS in pojdite na **Integrations**. Kliknite tri pike v zgornjem desnem kotu in izberite možnost **Custom Repositories**. Dodajte URL tega skladišča in kot kategorijo izberite **Integration**.

2. **Nastavi integracijo**
 Po dodajanju repozitorija poiščite "KronotermVoiceActions" v sistemu HACS v razdelku **Integrations**. Kliknite nanj in izberite **Install**.

3. **Zaženite Home Assistant**
 Ponovno zaženite Home Assistant, da prepozna novo integracijo.

4. **Dodajte integracijo**
 Pojdite na **Nastavitve > Naprave in storitve** v programu Home Assistant. Kliknite gumb "Add integration" in poiščite "KronotermVoiceActions". Sledite navodilom za konfiguracijo integracije.

## Konfiguracija

1. **Namestite pogovornega agenta:**
    * Pojdite v `Settings` > `Devices & services` in desno spodaj izberite `Add integration`. Poiščite `Kronoterm Wyoming`.. Kliknite nanj in izberite `Setup another instance of Kronoterm Wyoming` in končno izberite `Set up the custom Kronoterm conversation agent`.
2. **Namestite STT in TTS integracij:**
    * Vrnite se v `Devices & services`.
    * Vaša integracija **Kronoterm Wyoming - Whisper** ali pa **Piper** bi se moral pojaviti avtomatično.
    * Kliknite gumb **Add**.

3. **Začetek pogovora**
    * Pojdite v `Settings` > `Voice assistants` in kliknite `Add assistant`. Izberite ime in nastavite jezik na `Slovenian`. Nato za `Conversation Conversation Agent` izberite `Kronoterm Agent`. Za `Speech-to-text` izberite `faster-whisper`. V primeru da imate naložen **Piper** ga lahko izberete za `Text-to-speech`.
