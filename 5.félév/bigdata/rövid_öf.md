Itt a frissített, átrendezett és letisztult **Markdown tananyag / vizsga-cheatsheet**. A szerkezetet úgy alakítottam át, hogy **közvetlenül az RDD és a DataFrame API álljon a középpontban**, a kapcsolódó HDFS, Streaming és Kafka tudnivalók pedig tömör, gyorsan átlátható blokkokként támogassák azokat.

---

# 🚀 PySpark & Big Data Vizsga-Cheatsheet

---

## 1. 🔥 PySpark RDD (Resilient Distributed Dataset)

Az RDD a Spark alapszintű, immutábilis, elosztott adatszerkezete. Alacsony szintű vezérlést biztosít.

### 1.1. Inicializálás & Létrehozás

```python
from pyspark import SparkConf, SparkContext

# SparkContext inicializálása (egy futtatás során csak EGYSZER futtatható!)
conf = SparkConf().setMaster("spark://spark-master:7077").setAppName("ExamPrep")
sc = SparkContext(conf=conf)

# 1. Kollekcióból (parallelize)
rdd_num = sc.parallelize(range(20), numSlices=4)

# 2. HDFS szövegfájlból (textFile)
rdd_text = sc.textFile("hdfs://namenode:8020/data/raw/sensors/sensors10.json")

```

### 1.2. Transzformációk vs. Akciók

* **Transzformációk (Lusta / Lazy evaluation):** Nem futtatnak számítást azonnal, csak végrehajtási tervet (DAG) építenek.
* *Példák:* `map`, `flatMap`, `filter`, `reduceByKey`, `groupByKey`, `mapValues`, `sortBy`, `distinct`, `join`, `coalesce`, `repartition`.


* **Akciók (Action):** Elindítják a tényleges számítást a Spark klaszteren, és eredményt adnak vissza a Drivernek vagy fájlba írnak.
* *Példák:* `collect`, `take`, `count`, `first`, `reduce`, `fold`, `aggregate`, `saveAsTextFile`.



---

### 1.3. RDD Műveletek Gyorsszótára

| Művelet | Típus | Működés | Példa |
| --- | --- | --- | --- |
| `map(func)` | Transzformáció | 1-to-1 elemátalakítás. | `rdd.map(lambda x: x * 2)` |
| `flatMap(func)` | Transzformáció | 1-to-N átalakítás, a kapott listákat "kilapítja". | `rdd.flatMap(lambda line: line.split(","))` |
| `filter(func)` | Transzformáció | Megtartja a feltételnek megfelelő elemeket. | `rdd.filter(lambda x: x % 2 == 0)` |
| `distinct()` | Transzformáció | Duplikációk eltávolítása. |
| `reduceByKey(func)` | Transzformáció | **Ezt használd!** Kulcsonként összevonja az értékeket. Mapper oldalon elő-összesít (combine), így minimális a hálózati adatmozgás (shuffle). | `pairs.reduceByKey(lambda a, b: a + b)` |
| `groupByKey()` | Transzformáció | **Kerülendő!** Kulcsonként egy csoportba gyűjti az összes értéket elő-összesítés nélkül. Nagy adatnál Out-Of-Memory (OOM) hibaforrás. |
| `mapValues(func)` | Transzformáció | Csak a `(kulcs, érték)` pár érték részét módosítja, a kulcs változatlan marad. | `pairs.mapValues(lambda v: v + 10)` |
| `sortBy(keyfunc, asc)` | Transzformáció | Rendezés keyfunc alapján. | `rdd.sortBy(lambda x: x[1], False)` *(csökkenő)* |
| `join(other)` | Transzformáció | Belső (inner) join két kulcs-érték RDD között. További típusok: `leftOuterJoin`, `rightOuterJoin`, `fullOuterJoin`. |
| `repartition(N)` | Transzformáció | Újraparticionálás $N$ partícióra. Teljes shuffle-t végez (növelésre és csökkentésre is jó). | |
| `coalesce(N)` | Transzformáció | Partíciók számának **csökkentése** shuffle nélkül (sokkal hatékonyabb, mint a repartition). | |
| `cache()` | Művelet | Az első Akció lefutása után a memóriában tárolja az RDD-t. | |
| `glom()` | Transzformáció | Megmutatja az elemeket partíciókra bontva: `rdd.glom().collect()` |
| `collect()` | Akció | A teljes RDD-t a Driver memóriájába gyűjti *(csak kis adathalmaznál szabad!)*. | |
| `take(n)` | Akció | Visszaadja az első $n$ elemet listaként. | |
| `reduce(func)` | Akció | Az összes elemet egyetlen értékké vonja össze. | `rdd.reduce(lambda a, b: a + b)` |

---


### 1.4. Gyakorlati RDD Minták (Kódrészletek)

#### A. Szó-/Termékszámlálás & Top N keresés

```python
lines = sc.textFile("vasarlasok.txt")
top3 = lines.flatMap(lambda line: line.split(",")) \
            .map(lambda word: word.strip().lower()) \
            .map(lambda word: (word, 1)) \
            .reduceByKey(lambda a, b: a + b) \
            .sortBy(lambda x: x[1], False) \
            .take(3)

```

#### B. Átlag számítás `mapValues` + `reduceByKey` kombinációval

```python
# Bemenet: (kategória, érték) párok RDD-je
data = sc.parallelize([('A', 10), ('B', 30), ('B', 20), ('A', 10)])

avg_rdd = data.mapValues(lambda val: (val, 1)) \
              .reduceByKey(lambda a, b: (a[0] + b[0], a[1] + b[1])) \
              .mapValues(lambda x: round(x[0] / x[1], 2))
# Eredmény: [('A', 10.0), ('B', 25.0)]

```

#### C. Összetett aggregáció `aggregate()` segítségével (Min/Max egyszerre)

```python
rdd = sc.parallelize([10, 5, 20, 15, 30])

# (min, max) kezdőértékekkel
min_max = rdd.aggregate(
    (float('inf'), float('-inf')),
    lambda acc, x: (min(acc[0], x), max(acc[1], x)),      # Partíción belüli akkumulálás
    lambda a, b: (min(a[0], b[0]), max(a[1], b[1]))       # Partíciók közötti összevonás
)

```

---

## 2. ⚡ PySpark DataFrame API & Spark SQL

A DataFrame névvel ellátott oszlopokba szervezett elosztott adattábla. A **Catalyst Optimizer** automatikusan optimalizálja a végrehajtási tervét, így lényegesen hatékonyabb az RDD-nél.

### 2.1. SparkSession és Beolvasás/Kiírás

```python
from pyspark.sql import SparkSession
from pyspark.sql.functions import col, expr, avg, count, sum, min, max, desc, round, to_date
from pyspark.sql.types import StructType, StructField, StringType, IntegerType, DoubleType

spark = SparkSession.builder.appName("ExamApp").getOrCreate()

# 1. Explicit séma definíció
schema = StructType([
    StructField("sensor_id", StringType(), False), # False = NULL nem engedélyezett
    StructField("timestamp", StringType(), True),
    StructField("value", DoubleType(), True)
])

# 2. Beolvasás CSV / JSON fájlból
df_csv = spark.read.format("csv") \
    .option("header", True) \
    .option("inferSchema", True) \
    .load("hdfs://namenode:8020/data/raw/sensors/location")

df_json = spark.read.json("hdfs://namenode:8020/data/raw/sensors/sensors100.json")

# 3. Kiírás HDFS-re
# Alapértelmezés (több part-fájl jön létre a partíciók szerint):
df_csv.write.mode("overwrite").option("header", True).csv("hdfs://namenode:8020/output/loc")

# Kiírás egyetlen CSV fájlba (coalesce 1 használatával):
df_csv.coalesce(1).write.mode("overwrite").option("header", True).csv("hdfs://namenode:8020/output/loc_single")

```

---

### 2.2. Legfontosabb DataFrame Műveletek

```python
# 1. Oszlopkiválasztás és kifejezések
df.select("sensor_id", "value").show(5)
df.selectExpr("sensor_id", "concat(location, ' ', sensor_type) as LocSensor").show()

# 2. Szűrés (filter és where teljesen megegyezik)
# FONTOS: Bitenkénti operátorok (&, |, ~) és kötelező ZÁRÓJELEK a feltételeknél!
df.filter((col("location") == "Buda") & (col("value") > 20.0)).show()
df.where(~(col("location") == "Airport")).show()  # Tagadás: ~

# 3. Rendezés és egyedi értékek
df.orderBy(col("value").desc()).show(10)
df.select("location").distinct().show()

# 4. Összekapcsolás (Join)
# Típusok: "inner", "left", "right", "full"
df_joined = df.join(dfLoc, df.location == dfLoc.location, how="left").drop(dfLoc.location)

# Ha az oszlopnév mindkét táblában azonos:
df_joined = df.join(dfLoc, on="location", how="left")

# 5. Csoportosítás és aggregáció
df.groupBy("sensor_type").agg(
    count("*").alias("cnt"),
    round(avg("value"), 2).alias("avg_val"),
    max("value").alias("max_val")
).filter(col("avg_val") > 15).orderBy(desc("cnt")).show()

# 6. Spark SQL (Temp View)
df.createOrReplaceTempView("sensorTemp")
res_sql = spark.sql("""
    SELECT sensor_type, COUNT(*) as cnt, AVG(value) as avg_val
    FROM sensorTemp
    WHERE location != 'Airport'
    GROUP BY sensor_type
    HAVING avg_val > 10
    ORDER BY avg_val DESC
""")

# 7. Végrehajtási terv vizsgálata
res_sql.explain()

```

---

### 2.3. RDD és DataFrame Gyorsösszehasonlítás

| Jellemző | RDD (Low-Level API) | DataFrame (High-Level API) |
| --- | --- | --- |
| **Séma (Schema)** | Nincs (nyers Python objektumok/tuple-ök) | Van (névvel ellátott, típusos oszlopok) |
| **Optimalizáció** | Nincs automatikus optimalizáció | **Catalyst Optimizer** és **Tungsten** |
| **Ablakos műveletek** | Nehézkes (egyedi kulcsos logikák) | Beépített ablakkezelés (`window()`) |
| **Hibakeresés** | Nehezebb, fordítás idejű típusellenőrzés | Könnyebb, deklaratív lekérdezések |
| **Teljesítmény** | Lassabb Python feltételértékelés miatt | Gyorsabb (C++ szintű Java bytecode generálás) |

---

## 3. 🌊 Structured Streaming & Kafka Integráció

A **Structured Streaming** a DataFrame API-ra épülő, valós idejű adatfolyam-feldolgozó motor.

### 3.1. Kulcsfogalmak

* **Event Time vs. Processing Time:**
* *Event Time:* Az esemény saját rekordjában lévő időbélyeg (mikor keletkezett az adat).
* *Processing Time:* Az az időpont, amikor a Spark feldolgozza a rekordot.


* **Watermark (Vízjel):** Megadja, hogy a rendszer mennyi késést engedélyez az eseményeknél (*Event Time* alapon), mielőtt lezárja az ablakot és kidobja a régi állapotot a memóriából.
* `.withWatermark("event_time", "10 seconds")`


* **Output Mode-ok:**
* `append`: Csak az új, véglegesen lezárt eredményeket írja ki.
* `update`: Azokat a sorokat írja ki, amelyek frissültek a legutóbbi trigger óta.
* `complete`: Minden trigger alkalmával a teljes eredménytáblát újra kiírja.



---

### 3.2. Streaming Kódminták

#### A. Kafka Beolvasás és JSON Parse-olás (DataFrame)

```python
# Kafka Stream Beolvasása
kafka_raw = spark.readStream \
    .format("kafka") \
    .option("kafka.bootstrap.servers", "kafka:9092") \
    .option("subscribe", "sensors") \
    .option("startingOffsets", "latest") \
    .load()

# JSON sémához alakítás
sensor_schema = StructType([
    StructField("sensor_id", StringType()),
    StructField("timestamp", StringType()),
    StructField("type", StringType()),
    StructField("value", DoubleType())
])

parsed_stream = kafka_raw.select(
    expr("CAST(value AS STRING) as json_str")
).select(
    from_json("json_str", sensor_schema).alias("data")
).select("data.*")

```

#### B. Ablakos Aggregáció Vízjellel (DataFrame Streaming)

```python
alert_stream = parsed_stream \
    .withColumn("event_time", to_date(col("timestamp"))) \
    .withWatermark("event_time", "10 seconds") \
    .filter(col("type") == "temperature") \
    .groupBy(
        window(col("event_time"), "10 seconds", "5 seconds"), # 10s ablak, 5s csúszás
        col("sensor_id")
    ) \
    .agg(
        sum(expr("CASE WHEN value >= 80.0 THEN 1 ELSE 0 END")).alias("high_cnt")
    ) \
    .where("high_cnt >= 3")

query = alert_stream.writeStream \
    .format("console") \
    .outputMode("update") \
    .start()

```

#### C. Hybrid Megoldás: Streaming DataFrame átalakítása RDD-vé (`foreachBatch`)

```python
def process_microbatch(batch_df, batch_id):
    # A mikrobatch DataFrame átalakítása RDD-vé
    rdd = batch_df.rdd
    
    # Standard RDD műveletek végrehajtása az adott mikrobatchen
    top3 = rdd.map(lambda r: (r.sensor_id, r.value)) \
              .reduceByKey(lambda a, b: max(a, b)) \
              .sortBy(lambda x: x[1], False) \
              .take(3)
    
    print(f"--- Batch ID: {batch_id} ---")
    for item in top3:
        print(item)

# Indítás foreachBatch-el
query = parsed_stream.writeStream \
    .foreachBatch(process_microbatch) \
    .outputMode("append") \
    .start()

```

---

## 4. 🐘 HDFS & MapReduce Alapok (Gyors Áttekintés)

### 4.1. HDFS Architektúra

* **NameNode:** Metaadatokat kezeli a memóriában (milyen fájlok léteznek, mely blokkokból állnak és azok hol találhatók).
* **DataNode:** A tényleges adatblokkokat tárolja lemezen és kiszolgálja a kéréseket.
* **Blokkméret:** Élesben alapértelmezetten **128 MB** (oktatási környezetben **1 MB** a könnyebb demonstrációért).
* **Replikáció:** Alapértelmezetten 3-szoros. Biztosítja a hibatűrést.
* *Példa:* 2x-es replikációnál egy 100 MB-os fájl **200 MB** fizikai helyet foglal a HDFS-ben.
* *DataNode kiesés:* A NameNode szívverés (*heartbeat*) alapján érzékeli, a hiányzó blokkokat `under-replicated` állapotba teszi, majd automatikusan újrahasznosítja/másolja a meglévő replikákból.



### 4.2. Legfontosabb HDFS Parancsok

```bash
hdfs dfs -ls /data/raw/sensors                        # Könyvtár tartalmának listázása
hdfs dfs -mkdir -p /data/lab01                         # Könyvtár létrehozása
hdfs dfs -put -f sensors10.json /data/raw/sensors/     # Fájl feltöltése
hdfs dfs -du -h /data/raw/sensors                      # Tárhelyhasználat (du)
hdfs dfsadmin -report                                  # Cluster általános állapota
hdfs fsck /data/lab01/sensors100.json -files -blocks -locations # Blokkok helyének vizsgálata

```

---

## 5. 💡 Puskázható Kódsablonok & Vizsga-Tippek

### A. Leggyakoribb Hibalefutások & Megoldásuk

1. **Zárójelek hiánya DataFrame szűrésnél:**
* ❌ `df.where(df["a"] == 1 & df["b"] > 2)` $\rightarrow$ HIBÁS!
* ✅ `df.where((df["a"] == 1) & (df["b"] > 2))` $\rightarrow$ HELYES!


2. **SparkContext újraindítási hiba:**
* Ha a `sc = SparkContext(...)` sort többször futtatod egy notebookban, hiba keletkezik. Használd a Kernel Restart-ot!


3. **`groupByKey()` vs `reduceByKey()` RDD-ben:**
* Ha a feladat aggregációt kér (pl. összegzés, számlálás), **mindig `reduceByKey()`-t használj** a network shuffle csökkentése érdekében!



### B. Gyors Puskasablonok

```python
# --- RDD: Dátum szerinti átlaghőmérséklet ---
rdd.map(lambda row: (row["timestamp"].split("T")[0], (float(row["value"]), 1))) \
   .reduceByKey(lambda a, b: (a[0] + b[0], a[1] + b[1])) \
   .mapValues(lambda x: round(x[0] / x[1], 2))

# --- DataFrame: Átlag számítás kategóriánként, kizárással ---
df.where(~col("Category").isin(["Beverages", "Coffee & Tea"])) \
  .groupBy("Category") \
  .agg(round(avg("Calories"), 2).alias("avg_cal")) \
  .orderBy(desc("avg_cal"))

```