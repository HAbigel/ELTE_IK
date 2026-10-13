# Apache Spark (pyspark RDD) Gyakorlati Útmutató

A gyakorlat célja az **Apache Spark** architektúrájának megismerése, az **RDD (Resilient Distributed Dataset)** használata, a partícionálás és a gyorsítótárazás (`cache`) megértése, valamint az RDD transzformációk és akciók elmélyítése gyakorlati feladatokon keresztül.

---

## 1. Architektúra és Alapfogalmak

A Spark egy elosztott, memóriában futó adatalapú feldolgozókeretrendszer.

| Fogalom | Szerep és Működés |
| --- | --- |
| **Driver** | A Spark alkalmazást vezérlő főprogram (jelen esetben a Jupyter notebook). |
| **Master** | A Spark klaszter erőforrás-koordinátora (vezérlője). |
| **Worker** | A klaszter számítási csomópontja, amely az elvégzendő feladatokat futtatja. |
| **Job** | Egy Spark **action** által elindított teljes feldolgozási egység. |
| **Stage** | A Job adatáramlási szakaszokra bontott része (pl. shuffle határok mentén). |
| **Task** | Egy stage egy konkrét **partícióján** végrehajtott egyedi számítási munka. |
| **Partition** | Az RDD adatainak egy logikai egysége, amelyet egyetlen task dolgoz fel a memóriában. |

---

## 2. Környezet Elindítása és Előkészítése

1. **Jupyter image újraépítése és elindítása:** Host gépen (CMD).
Mivel a Jupyter és a Spark Worker Python verzióinak meg kell egyezniük, építsd újra a konténert:

```cmd
docker compose --profile all build --no-cache jupyter
scripts\lesson-02-start.cmd

```


2. **Jupyter Notebook és Spark Master megnyitása:** Böngészőben.
* **Jupyter Notebook:** `http://localhost:8888` (Jelszó: `12345678`)
* **Spark Master UI:** `http://localhost:8080`
* Nyisd meg a **`gyak1_temp.ipynb`** notebookot.


3. **SparkContext inicializálása:** Jupyter Notebook-ban.
```python
from pyspark import SparkConf, SparkContext
from pyspark.sql import SparkSession
from pyspark.sql.functions import avg, min, max, count
import json

conf = SparkConf().setMaster("spark://spark-master:7077")
sc = SparkContext(conf=conf)

```

> **Figyelem:** Ne futtasd újra ezt a cellát, ha a `SparkContext` már létrejött! Szükség esetén indítsd újra a notebook kernelt.


---

## 3. RDD Kezelés, Partíciók és Cache

### RDD Létrehozása

* **Memóriából (parallelize):** `rdd = sc.parallelize(range(20))`
* **HDFS-ből:**
```python
rdd2 = sc.textFile("hdfs://namenode:8020/data/raw/sensors/sensors10.json")

```



### Cache Működése

A `.cache()` elmenti a részeredményt a memóriába, így a többszöri feldolgozás lényegesen gyorsabb. A számítás **lusta kiértékelésű (lazy evaluation)**, azaz csak az első **action** (pl. `.collect()`, `.count()`, `.first()`) hatására fut le.

```python
rdd = sc.parallelize(range(10)).cache()
print(rdd.collect()) # Az action indítja el a tényleges kiszámítást és cache-elést

```

### Partícionáló Függvények

A `.glom()` paranccsal megtekinthető az RDD elemeinek partíciónkénti megoszlása: `rdd.glom().collect()`.

| Függvény | Működés és Jellemzők |
| --- | --- |
| **`repartition(n)`** | Újrapartícionál tetszőleges $n$ számra. **Shuffle-t (hálózati adatmozgatást) vált ki**. |
| **`coalesce(n)`** | Partíciószám csökkentésére szolgál. Optimalizált, tipikusan **shuffle nélkül** vonja össze a partíciókat. |
| **`glom()`** | Kimenetként a partíciók elemeit tömbökbe/listákba szervezve adja vissza. |

---

## 4. Legfontosabb RDD Műveletek Összefoglalója

### Alapvető Transzformációk és Akciók

* **`map(func)`**: Minden elemet egyenként átalakít.
* **`flatMap(func)`**: Elemenként listát vár, majd a kimeneti listákat egyetlen lapos RDD-vé fűzi össze.
* **`filter(func)`**: Csak a feltételnek megfelelő (`True`) elemeket tartja meg.
* **`distinct()`**: Eltávolítja a duplikátumokat.
* **`sortBy(keyfunc)`**: Rendezés megadott kulcs/szempont szerint.

### Kulcs-Érték Párok Műveletei (`PairRDD`)

* **`reduceByKey(func)`**: Az azonos kulcsú értékeket összevonja a megadott aggregációs függvénnyel. **Elő-összesítést (combiner) végez a node-okon, így sokkal hatékonyabb.**
* **`groupByKey()`**: Csoportosítja az azonos kulcsú elemeket egy listába. **Kerülendő nagy adathalmazoknál**, mert nem végez elő-összesítést, és memóriahiányt (OOM) okozhat.

```python
# Példa átlagszámításra reduceByKey segítségével
data = [('x', 10), ('y', 30), ('y', 20), ('x', 10)]
r = sc.parallelize(data)

avg_rdd = r.mapValues(lambda x: (x, 1)) \
           .reduceByKey(lambda a, b: (a[0] + b[0], a[1] + b[1])) \
           .mapValues(lambda x: x[0] / x[1])

print(avg_rdd.collect()) # [('x', 10.0), ('y', 25.0)]

```

### Összekapcsolások (Join-ok)

* `r1.join(r2)`: Belső kapcsolat (Inner join)
* `r1.leftOuterJoin(r2)`: Bal oldali külső kapcsolat
* `r1.rightOuterJoin(r2)`: Jobb oldali külső kapcsolat
* `r1.fullOuterJoin(r2)`: Teljes külső kapcsolat

### Komplett Aggregációk (`fold`, `aggregate`)

* **`reduce(func)`**: A teljes RDD elemeit vonja össze egyetlen értékké (asszociatív és kommutatív kell legyen).
* **`fold(zeroValue, op)`**: Hasonló a `reduce`-hoz, de megadható egy kezdőérték (`zeroValue`), amely minden partíción és a végső összevonáskor is hozzáadódik.
* **`aggregate(zeroValue, seqOp, combOp)`**: Lehetővé teszi, hogy a kimeneti típus eltérjen a bemeneti típustól (például egyszerre számol összeget és darabszámot, vagy min/max értéket).

---

## 5. Múlt Heti Osztályozási Feladat Spark RDD-vel

Az `Airport` helyszín `temperature` adatait kategorizáljuk, majd kategóriánként megszámoljuk az **egyedi napok** számát:

```python
rdd = sc.textFile("hdfs://namenode:8020/data/raw/sensors/sensors100.json")

def jsonToKeyValue(data):
    date = data["timestamp"].split("T")[0]
    value = data["value"]

    if value < 10:
        group = "<10"
    elif value <= 20:
        group = "10-20"
    elif value <= 30:
        group = "20-30"
    else:
        group = ">30"

    return (group, date)

result = (
    rdd
    .map(lambda x: json.loads(x))
    .filter(lambda x: x["location"] == "Airport" and x["sensor_type"] == "temperature")
    .map(jsonToKeyValue)
    .distinct()                 # Egyedi (kategória, dátum) párok szűrése
    .mapValues(lambda x: 1)     # (kategória, 1) formátum
    .reduceByKey(lambda a, b: a + b)
    .collect()
)

print(result)

```

---

## 6. Önálló Feladatok Megoldása

### Önálló Feladat A: A legmelegebb nap megkeresése

**Feladat:** Keresd meg azt a napot, amikor a legmagasabb hőmérsékletet mérték (szűrve az `Airport` + `temperature` rekordokra).

```python
import json

rdd = sc.textFile("hdfs://namenode:8020/data/raw/sensors/sensors100.json")

# 1. Beolvasás, szűrés és transzformáció (dátum, hőmérséklet) párokra
airport_temps = (
    rdd
    .map(lambda x: json.loads(x))
    .filter(lambda x: x["location"] == "Airport" and x["sensor_type"] == "temperature")
    .map(lambda x: (x["timestamp"].split("T")[0], x["value"]))
)

# Megoldás 1: reduce segítségével (legnagyobb érték kiválasztása)
max_day_reduce = airport_temps.reduce(lambda a, b: a if a[1] > b[1] else b)
print("Legmelegebb nap (reduce):", max_day_reduce)

# Megoldás 2: sortBy segítségével (csökkenő sorrend és első elem vétele)
max_day_sort = airport_temps.sortBy(lambda x: x[1], ascending=False).first()
print("Legmelegebb nap (sortBy):", max_day_sort)

```

---

### Önálló Feladat B: Napi átlaghőmérséklet kiszámítása

**Feladat:** Számítsd ki az `Airport` helyszín napi átlaghőmérsékleteit, rendezd dátum szerint, és határozd meg a legmelegebb, valamint a leghidegebb napi átlagot!

```python
import json

rdd = sc.textFile("hdfs://namenode:8020/data/raw/sensors/sensors100.json")

# 1. (Dátum, (érték, 1)) pár képezése a szűrt adatokból
daily_stats = (
    rdd
    .map(lambda x: json.loads(x))
    .filter(lambda x: x["location"] == "Airport" and x["sensor_type"] == "temperature")
    .map(lambda x: (x["timestamp"].split("T")[0], (x["value"], 1)))
    .reduceByKey(lambda a, b: (a[0] + b[0], a[1] + b[1]))  # Összegek és darabszámok összeadása
    .mapValues(lambda x: round(x[0] / x[1], 2))             # Átlag kiszámítása 2 tizedes pontossággal
    .cache()
)

# 2. Rendezés dátum szerint
sorted_by_date = daily_stats.sortBy(lambda x: x[0]).collect()
print("Napi átlagok dátum szerint rendezve (első 5):", sorted_by_date[:5])

# 3. Legmelegebb napi átlag
hottest_avg = daily_stats.reduce(lambda a, b: a if a[1] > b[1] else b)
print("Legmagasabb napi átlag:", hottest_avg)

# 4. Leghidegebb napi átlag
coldest_avg = daily_stats.reduce(lambda a, b: a if a[1] < b[1] else b)
print("Legalacsonyabb napi átlag:", coldest_avg)

```