# Hadoop Distributed File System (HDFS) és MapReduce Gyakorlati Útmutató

A gyakorlat célja a HDFS elosztott működésének megértése: a fájlok blokkokra bontása, a replikáció, a DataNode-ok kiesésének kezelése és a MapReduce alapú adattervezés.

---

## 1. Elméleti Alapfogalmak

| Componens / Fogalom | Szerep és Működés |
| --- | --- |
| **NameNode** | A HDFS **metaadat-kezelője**. Térképként működik: nyilvántartja a könyvtárstruktúrát, a fájlok blokkjait és azok fizikai elhelyezkedését. |
| **DataNode** | A **tényleges adatblokkokat** tárolja és szolgálja ki a worker csomópontokon. |
| **HDFS Blokk** | A fájlok rögzített méretű szeletei. Alapértelmezett mérete **128 MB** (ebben a laborkörnyezetben oktatási céllal **1 MB**). |
| **Replikáció** | Egy blokk több DataNode-on is elmentésre kerül a hibatűrés (redundancia) biztosítására. |

---

## 2. Környezet Elindítása és Előkészítése

1. **Docker környezet indítása:** Host gépen (CMD).
Töltsd le a szükséges image-eket és indítsd el a konténereket:

```cmd
docker compose --profile all pull
scripts\lesson-01-start.cmd

```

*(Megjegyzés: Az első indítás a letöltések miatt több percig is eltarthat.)*


2. **Szenzoradatok generálása:** Host gépen (bigdata-gyak\data\historical).
Hozz létre tesztfájlokat a generátor segítségével:

```cmd
python sensor-generator.py --size 10MB --output sensors10.json
python sensor-generator.py --size 100MB --output sensors100.json

```


3. **Belépés a NameNode-ba és HDFS könyvtárak létrehozása:** Host gépen (CMD).
Lépj be a NameNode konténerbe, majd hozd létre a szükséges mappastruktúrát:

```bash
docker compose exec -it namenode bash

# Saját felhasználói könyvtár és adatkönyvtárak létrehozása
hdfs dfs -mkdir -p /user/root
hdfs dfs -mkdir -p /data/raw/sensors /data/reference

```


4. **Adatok feltöltése a HDFS-be:** NameNode konténeren belül.
Töltsd fel a 10 MB-os fájlt a HDFS-be:

```bash
hdfs dfs -put -f /course-data/historical/sensors10.json /data/raw/sensors/
hdfs dfs -ls /data/raw/sensors

```


> **Monitoring:** A NameNode webes felülete a **`http://localhost:9870`** címen érhető el.
> * **Configured Capacity / DFS Used:** Kapacitás és kihasználtság.
> * **Live Nodes:** Aktív DataNode-ok száma.
> * **Utilities → Browse the file system:** Fájlok, blokkok és replikák böngészése.
> 
> 

---

## 3. Diagnosztikai és Állapotvizsgáló Parancsok

A HDFS állapotát és a tárolási struktúrát az alábbi parancsokkal ellenőrizheted:

* **Cluster állapotának jelentése:**
```bash
hdfs dfsadmin -report

```


* **Fájl tárhelyigényének ellenőrzése:**
```bash
hdfs dfs -du -h /data/raw/sensors

```


*(Kettős replikáció esetén a fizikai helyfoglalás a fájlméret kétszerese.)*
* **Blokkok és DataNode helyszínek vizsgálata:**
```bash
hdfs fsck /data/raw/sensors/sensors10.json -files -blocks -locations

```



---

## 4. Hibatűrés Vizsgálata (DataNode Kiesése)

1. **DataNode1 leállítása (Host CMD):**
```cmd
docker compose stop datanode1

```


2. **Kiesés érzékelése:**
A `hdfs dfsadmin -report` futtatásakor a DataNode nem tűnik el azonnal. A NameNode a hiányzó *heartbeat* üzenetek alapján, egy időkorlát (timeout) után jelöli csak kiesettnek (`Dead`).
3. **Adatelérés és írás szimulációja:**
* **Olvasás test:** A fájl továbbra is elérhető a megmaradt replikákból:
```bash
hdfs dfs -head /data/raw/sensors/sensors10.json

```


* **Új feltöltés felülbírált blokkmérettel:**
```bash
hdfs dfs -D dfs.blocksize=67108864 -put /course-data/historical/sensors100.json /data/raw/sensors/

```


* **Under-replicated állapot:** A report jelzi, ha a blokkok nem érik el az előírt replikációs tényezőt.


4. **Helyreállítás:**
```cmd
docker compose start datanode1

```


A DataNode újracsatlakozása után a NameNode automatikusan szinkronizálja és helyreállítja a hiányzó replikákat.

---

## 5. Önálló Feladat Útmutató

### Task 1: Könyvtár és adatfeltöltés

```bash
# 1. Könyvtár létrehozása és ellenőrzése
hdfs dfs -mkdir -p /data/lab01
hdfs dfs -ls /data/

# 2. 100 MB-os fájl feltöltése
hdfs dfs -put /course-data/historical/sensors100.json /data/lab01/
hdfs dfs -ls /data/lab01/

# 3. Blokkszerkezet elemzése
hdfs fsck /data/lab01/sensors100.json -files -blocks -locations

```

---

### Task 2: MapReduce Logika Megtervezése

A feladat az `Airport` helyszínhez tartozó `temperature` mérések alapján meghatározni a különböző hőmérsékleti kategóriákba tartozó **egyedi napok** számát.

#### Hőmérsékleti kategóriák:

* **`<10°C`**
* **`10-20°C`**
* **`20-30°C`**
* **`>30°C`**

#### A feldolgozási folyamat (MapReduce architektúra)

```
[ Bemeneti fájl (HDFS blokkok) ]
               │
               ▼
   ┌───────────────────────┐
   │        MAPPER         │  1. Szűrés: location == "Airport" AND type == "temperature"
   │                       │  2. Dátum kinyerése: YYYY-MM-DD
   │                       │  3. Kategória meghatározása
   └───────────┬───────────┘
               │  Kimenet: Key = (Kategória, Dátum), Value = 1
               ▼
   ┌───────────────────────┐
   │  SHUFFLE & SORT       │  A Hadoop a kulcsok (Kategória, Dátum) alapján 
   │  (Keretrendszer)      │  csoportosítja és rendezi az adatokat.
   └───────────┬───────────┘
               │
               ▼
   ┌───────────────────────┐
   │        REDUCER        │  1. Az azonos (Kategória, Dátum) kulcsokból csak 1 napot számol.
   │                       │  2. Összesíti a napokat kategóriánként.
   └───────────┬───────────┘
               │
               ▼
      [ Elvárt Kimenet ]

```

---

### Segítő Kérdések Megválaszolása (Tervezési Szempontok)

1. **Hogyan lehet a timestamp értékből csak a dátumot kinyerni?**
* A szöveges/JSON rekordból a dátum mező első 10 karakterének levágásával (pl. `YYYY-MM-DD`), vagy a dátum-idő objektum formázásával.


2. **Hogyan döntöd el, melyik hőmérsékleti kategóriába tartozik egy mérés?**
* Egyszerű feltételkezeléssel (`if/else` ágakkal):
* $T < 10$ $\rightarrow$ `<10`
* $10 \le T < 20$ $\rightarrow$ `10-20`
* $20 \le T \le 30$ $\rightarrow$ `20-30`
* $T > 30$ $\rightarrow$ `>30`




3. **Hogyan biztosítod, hogy egy napot egy kategóriában csak egyszer számoljunk?**
* A **Mapper kimenetének összetett kulccsá** alakításával: `(Kategória, Dátum)`. Mivel a Shuffle & Sort fázis összevonja az azonos kulcsokat, a Reducer egy adott `(Kategória, Dátum)` párra csak egyetlen kulcs-csoportot kap meg, függetlenül attól, hány mérés volt aznap.


4. **Mi legyen a Mapper kimenetének kulcsa és értéke?**
* **Kulcs:** `(Kategória, Dátum)` pár (pl. `("10-20", "2026-09-04")`)
* **Érték:** `1` (vagy üres érték)


5. **Mi legyen a Reducer feladata?**
* A Reducer megkapja az összetett kulcsot `(Kategória, Dátum)`.
* Megszámolja, hány egyedi dátum tartozik az egyes kategóriákhoz, majd kategóriánként összesítve írja ki a végeredményt.


6. **Miért lehet előnyös, ha a feldolgozás a HDFS-ben lévő adatokhoz közel történik?**
* Ez a **Data Localities** (adat-közelség) elve. A hálózati adatforgalom a szűk keresztmetszet a nagy adatmennyiségeknél; ha a számítás (Mapper) azon a DataNode-on fut, ahol a blokk amúgy is tárolva van, nincs szükség gigabájtok hálózaton keresztüli átvitelére.