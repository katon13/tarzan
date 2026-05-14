# TFD — aktualizacja ustawień Nextion `settings_main`

## Cel zmiany

Do fizycznego Nextiona dodano obsługę ustawień tekstowych dla ekranu TFD / TAKE.

Strona `settings_main` ma służyć do wpisania danych opisowych ujęcia:

```text
TITLE / tytuł filmu
DIRECTOR / reżyser filmu
```

Te dane mają później być wyświetlane na stronie `take_main` w polach tytułu i reżysera.

---

## Zasada architektury

Ta zmiana nie tworzy nowego źródła danych ruchu.

Źródłem prawdy dla TFD nadal pozostają:

```text
PAR
SignalBus
TAKE
osie
czujniki
```

Dane wpisane na `settings_main` są tylko metadanymi opisowymi TAKE / TFD:

```text
title
director
```

CLAP pozostaje jedynym dodatkowym markerem synchronizacyjnym TFD.

---

## Strona `settings_main`

Na stronie `settings_main` dodano dwa globalne pola tekstowe z przypisaną klawiaturą ekranową Nextion:

```text
t_title
t_director
```

Ważne ustawienie:

```text
Scope / vscope = global
Associated Keyboard = 1
Input Type = character
```

To jest wymagane, ponieważ klawiatura ekranowa Nextion wymaga globalnego zakresu pola, z którym jest powiązana.

---

## Pole tytułu filmu

Komponent:

```text
t_title
```

Rola:

```text
wpisanie tytułu filmu / TAKE
```

Ustawienia robocze:

```text
Scope: global
Associated Keyboard: 1
Input Type: character
Max. Text Size: 150
```

---

## Pole reżysera

Komponent:

```text
t_director
```

Rola:

```text
wpisanie reżysera filmu / TAKE
```

Ustawienia robocze:

```text
Scope: global
Associated Keyboard: 1
Input Type: character
Max. Text Size: 150
```

---

## Przycisk zapisu metadanych

Na stronie `settings_main` dodano przycisk:

```text
b_save_meta
```

Przycisk wysyła teksty do systemu TARZAN przez standardowe komendy Nextion `print`, `prints` i `printh FF FF FF`.

Kod zdarzenia `Touch Release Event`:

```text
print "set:title="
prints t_title.txt,0
printh FF FF FF
print "set:director="
prints t_director.txt,0
printh FF FF FF
```

---

## Komunikaty wysyłane z Nextiona

Po naciśnięciu `b_save_meta` Nextion wysyła:

```text
set:title=<tekst z t_title>
set:director=<tekst z t_director>
```

Te komunikaty powinny być obsłużone po stronie Python / bridge tak samo prosto jak istniejące komunikaty tekstowe z Nextiona.

Nie należy budować osobnego protokołu.

---

## Relacja z `take_main`

Strona `take_main` ma wyświetlać wpisane metadane w istniejących polach:

```text
t1 = tytuł filmu
t2 = reżyser filmu
```

Python / bridge powinien po odebraniu metadanych z `settings_main` wysyłać je do fizycznego Nextiona na `take_main` przez standardowe komendy:

```text
t1.txt="..."
t2.txt="..."
```

---

## Kodowanie tekstu

Na fizycznym Nextionie ustawienia fontów i kodowanie pozostają po stronie projektu HMI.

Problem ewentualnego psucia polskich znaków ma być rozwiązany po stronie Pythona / bridge, czyli przy wysyłaniu tekstów do Nextiona.

Nie należy zmieniać działającego ustawienia fizycznego Nextiona bez potrzeby.

---

## Granice tej zmiany

Ta aktualizacja dokumentuje tylko zmiany wykonane na fizycznym Nextionie w stronie `settings_main`.

Nie obejmuje:

```text
- przebudowy TFD
- przebudowy bridge
- zmiany RRP
- zmiany XYZ
- zmiany TAKE save/load
- zmiany generatora STEP/DIR
- zmiany mechaniki osi
```

---

## Minimalny zakres implementacji po stronie Python

Późniejsza implementacja powinna ograniczyć się do:

```text
1. odebrania komunikatu set:title=
2. odebrania komunikatu set:director=
3. zapisania tych wartości jako metadanych TFD/TAKE
4. wysłania ich na take_main do t1 i t2
```

Komunikacja ma używać wyłącznie standardowych komend Nextion już używanych w projekcie:

```text
component.txt="..."
print "..."
prints component.txt,0
printh FF FF FF
sendme
page <page_name>
```
