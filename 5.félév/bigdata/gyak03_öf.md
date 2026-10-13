# Spark SQL és DataFrame API Gyakorlati Útmutató

A gyakorlat célja a **SparkSession** használatának, a **DataFrame API** alapvető transzformációinak és aggregációinak, a **HDFS I/O** műveleteknek, valamint a **Spark SQL** kifejezéseknek és a **végrehajtási terveknek (`explain()`)** az elsajátítása.

---

## 1. Architektúra és Belépési Pont

| Fogalom / API | Szerep és Leírás |
| --- | --- |
| **SparkSession** | A Spark SQL és DataFrame API központi belépési pontja (`spark`). Ezen keresztül hozunk létre DataFrame-eket, futtatunk SQL lekérdezéseket és olvasunk/írunk adatokat. |
| **DataFrame** | Névvel ellátott oszlopokba szervezett, elosztott adathalmaz (sémával rendelkező RDD absztrakció). |
| **StructType & StructField** | Explicit sémaleíró osztályok, amelyek meghatározzák az oszlopok nevét, típusát és NULL-hatóságát. |
| **Temp View** | In-memory szimbolikus nézet, amely lehetővé teszi SQL lekérdezések futtatását a DataFrame-eken az adott `SparkSession`-ön belül. |

---

## 2. Környezet Előkészítése és DataFrame-ek Létrehozása

1. **SparkSession Inicializálása (Feladat 1):** Jupyter Notebook.
```python
from pyspark.sql import SparkSession
from pyspark.sql.functions import avg, min, max, count, sum, to_date, col, concat, lit
from pyspark.sql.types import StructType, StructField, StringType, IntegerType

spark = SparkSession.builder.appName("BigDataGyak").getOrCreate()

# Spark verzió ellenőrzése
print("Spark verzió:", spark.version)

```

> **Monitoring:** A Spark Master UI elérhető a `http://localhost:8080` címen.


2. **In-Memory DataFrame & Explicit Séma (Feladat 2 & 3):** Python kollekcióból.
Adatok kiegészítése a `country` oszloppal és explicit séma definíció:

```python
valuesLoc = [
    ("Buda", "Budapest", 1, "Hungary"),
    ("Pest", "Budapest", 2, "Hungary"),
    ("Obuda", "Budapest", 3, "Hungary"),
    ("Airport", "Budapest", 4, "Hungary")
]

LocSchema = StructType([
    StructField("location", StringType(), False),
    StructField("city", StringType(), True),
    StructField("id", IntegerType(), False),
    StructField("country", StringType(), True)
])

dfLoc = spark.createDataFrame(valuesLoc, LocSchema).cache()
dfLoc.printSchema()
dfLoc.show()

```


3. **CSV Kiírás és Beolvasás (Feladat 4, 5 & 6):** HDFS I/O.
```python
# 1. Kiírás több partícióval
dfLoc.write.mode("overwrite") \
    .option("header", True) \
    .format("csv") \
    .save("hdfs://namenode:8020/data/raw/sensors/location")

# 2. Kiírás egyetlen part-fájlba (coalesce)
dfLoc.coalesce(1).write.mode("overwrite") \
    .option("header", True) \
    .format("csv") \
    .save("hdfs://namenode:8020/data/raw/sensors/location_single")

# 3. CSV Beolvasás inferSchema segítségével
dfLoc_read = spark.read.format("csv") \
    .option("header", True) \
    .option("inferSchema", True) \
    .load("hdfs://namenode:8020/data/raw/sensors/location")

dfLoc_read.printSchema()

```


4. **Szenzoradatok beolvasása (Feladat 7):** JSON Beolvasás.
```python
df = spark.read.json("hdfs://namenode:8020/data/raw/sensors/sensors100.json")
df.printSchema()
df.show(5)
print("Rekordok száma:", df.count())

```


---

## 3. DataFrame Operációk és Transzformációk

### Join Típusok és Viselkedésük (Feladat 8 & 9)

```python
# Összekapcsolás (Left Join)
dfAll = df.join(dfLoc, on="location", how="left").cache()
dfAll.show(5)

```

| Join Típus | Leírás |
| --- | --- |
| **`inner`** | Csak azokat a sorokat tartja meg, amelyek mindkét DataFrame-ben megtalálhatók. |
| **`left`** | A bal oldali DataFrame összes sora megmarad, a nem illeszkedő jobb oldali mezők `NULL` értéket kapnak. |
| **`right`** | A jobb oldali DataFrame összes sora megmarad. |
| **`full`** | Mindkét oldal összes rekordját megőrzi. |

---

### Lekérdezési Műveletek Összefoglalása (Feladat 10–15)

```python
# Select & SelectExpr (Feladat 10 & 11)
dfAll.select("sensor_id", "location", "sensor_type", "value").show(3)

dfAll.selectExpr(
    "*",
    "concat(sensor_id, '_', location) as SensorLocation"
).show(3)

df.selectExpr("avg(value) as AvgValue", "count(distinct(sensor_id)) as UniqueSensors").show()

# Filter & Where (Feladat 12)
df.filter(df["location"] == "Airport").show(2)
df.where((df["location"] == "Buda") & (df["sensor_type"] == "temperature")).show(2)
df.where((df["sensor_type"] == "temperature") & ~(df["location"] == "Buda")).show(2)

# Distinct & OrderBy (Feladat 13 & 14)
df.select("location").distinct().show()
df.orderBy(df["value"].desc()).show(5)

# GroupBy & Aggregáció (Feladat 15)
df.groupBy("sensor_type").agg(
    count("*").alias("RecordCount"),
    avg("value").alias("AvgValue"),
    min("value").alias("MinValue"),
    max("value").alias("MaxValue")
).filter("AvgValue > 20").show()

```

---

## 4. Temp View, Spark SQL és Végrehajtási Terv (`explain`)

A Spark SQL és a DataFrame API ugyanazt a katalizátor optimalizálót (Catalyst Optimizer) használja.

```python
# Temp View létrehozása (Feladat 15)
df.createOrReplaceTempView("sensorTemp")

# SQL Lekérdezés
sql_df = spark.sql("""
    SELECT sensor_type, count(*) as cnt
    FROM sensorTemp
    GROUP BY sensor_type
""")
sql_df.show()

# Végrehajtási terv összehasonlítása (Feladat 16)
spark.sql("SELECT sensor_type, count(*) FROM sensorTemp GROUP BY sensor_type").explain()
df.groupBy("sensor_type").count().explain()

```

> **Gyakorlati tanulság:** A `explain()` kimenete mindkét esetben azonos **Logical Plan** és **Physical Plan** struktúrát mutat. Ez bizonyítja, hogy a Spark SQL és a DataFrame API teljesítménye és végrehajtási logikája teljesen megegyezik.

---

## 5. Önálló Feladatok Megoldása

### Önálló Feladat A: Mérési darabszámok szenzoronként (DataFrame API)

**Feladat:** Határozd meg, hogy az egyes `sensor_id`-k hány rekordot adtak, és rendezd csökkenő sorrendbe!

```python
sensor_counts = (
    df
    .groupBy("sensor_id")
    .count()
    .orderBy(col("count").desc())
)

sensor_counts.show(10)

```

---

### Önálló Feladat B: Legmelegebb nap RDD API-val

**Feladat:** Keresd meg a legmagasabb hőmérsékletű napot Budapest (Airport/Buda/Pest/Obuda) `temperature` mérései alapján RDD használatával!

```python
import json

rdd = sc.textFile("hdfs://namenode:8020/data/raw/sensors/sensors100.json")

budapest_locations = {"Buda", "Pest", "Obuda", "Airport"}

hottest_day_rdd = (
    rdd
    .map(lambda x: json.loads(x))
    .filter(lambda x: x["location"] in budapest_locations and x["sensor_type"] == "temperature")
    .map(lambda x: (x["timestamp"].split("T")[0], x["value"]))
    .reduce(lambda a, b: a if a[1] > b[1] else b)
)

print("Legmelegebb nap Budapesten (RDD):", hottest_day_rdd)

```

---

### Önálló Feladat C: Legmelegebb nap DataFrame API-val

**Feladat:** Oldd meg az előző feladatot DataFrame API segítségével (`to_date()`, `filter()`, `orderBy()`)!

```python
from pyspark.sql.functions import to_date, col

hottest_day_df = (
    df
    .filter((col("sensor_type") == "temperature") & (col("location").isin(["Buda", "Pest", "Obuda", "Airport"])))
    .withColumn("date", to_date(col("timestamp")))
    .select("date", "value", "location", "sensor_id")
    .orderBy(col("value").desc())
    .first()
)

print("Legmelegebb nap Budapesten (DataFrame):", hottest_day_df["date"], "Hőmérséklet:", hottest_day_df["value"])

```

---

### Önálló Feladat D: Budapest napi átlaghőmérséklete RDD-vel

**Feladat:** Számítsd ki Budapest napi átlaghőmérsékletét RDD segítségével a `(date, (value, 1))` mintát követve!

```python
import json

rdd = sc.textFile("hdfs://namenode:8020/data/raw/sensors/sensors100.json")

budapest_locations = {"Buda", "Pest", "Obuda", "Airport"}

bp_daily_avg_rdd = (
    rdd
    .map(lambda x: json.loads(x))
    .filter(lambda x: x["location"] in budapest_locations and x["sensor_type"] == "temperature")
    .map(lambda x: (x["timestamp"].split("T")[0], (x["value"], 1)))
    .reduceByKey(lambda a, b: (a[0] + b[0], a[1] + b[1]))
    .mapValues(lambda x: round(x[0] / x[1], 2))
    .sortBy(lambda x: x[0])
)

print("Budapest napi átlaghőmérsékletei (első 5 nap):")
for day in bp_daily_avg_rdd.take(5):
    print(day)

```