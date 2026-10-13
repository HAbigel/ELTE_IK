Közvetlenül a vizsga előtt már **ne elméletet magolj**, hanem a **típusfintákat, szintaktikai buktatókat és a mintakódok struktúráját** rögzítsd a fejedben.

Itt van a **10 legfontosabb pont**, amit érdemes az utolsó fél órában átfutnod:

---

### 1. Az RDD vs. DataFrame szűrés szintaxisa (A leggyakoribb hibatípus!)

* **DataFrame (Kötelező a zárójel és a bitenkénti operátor!):**
```python
# ❌ HIBÁS: df.filter(df.location == "Buda" and df.value > 20)
# ✅ HELYES:
df.filter((col("location") == "Buda") & (col("value") > 20.0))
df.where(~(col("location") == "Airport"))  # Tagadás: ~

```


* **RDD (Sima Python logikai operátorok):**
```python
rdd.filter(lambda x: x["location"] == "Buda" and x["value"] > 20.0)

```



---

### 2. A `reduceByKey()` kötelező mintája (RDD)

Átlagos érték számítása kulcsonként (`(összeg, darab)` pár képzése):

```python
# 1. Képezzük az alapot: (kulcs, (érték, 1))
# 2. reduceByKey: összeadjuk az értékeket és a darabszámokat
# 3. mapValues: kiszámoljuk az átlagot (összeg / darab)

rdd.map(lambda x: (x["category"], (float(x["value"]), 1))) \
   .reduceByKey(lambda a, b: (a[0] + b[0], a[1] + b[1])) \
   .mapValues(lambda x: round(x[0] / x[1], 2))

```

> **Jegyezd meg:** Nincs `groupByKey()`, mert az lassú és memória-hibát (OOM) okozhat! Mindig `reduceByKey()`.

---

### 3. A `flatMap()` vs. `map()` különbség (RDD)

* `map()`: 1 elemből **1 elemet** csinál (a lista egyben marad).
* `flatMap()`: 1 elemből **N elemet** csinál – kilapítja a listát.

```python
# Vesszővel elválasztott elemek szétvágása
rdd.flatMap(lambda line: line.split(",")) \
   .map(lambda word: word.strip().lower())

```

---

### 4. DataFrame aggregáció és oszlop átnevezés (`agg` + `alias`)

Több aggregációs függvény egyidejű használata `groupBy` után:

```python
from pyspark.sql.functions import col, avg, count, max, round, desc

df.groupBy("Category") \
  .agg(
      count("*").alias("cnt"),
      round(avg("Calories"), 2).alias("avg_cal"),
      max("Calories").alias("max_cal")
  ) \
  .orderBy(desc("avg_cal"))

```

---

### 5. DataFrame összekapcsolás (Join)

* Ha az oszlopnevek **különböznek**:
```python
df1.join(df2, df1.Category == df2.Id, how="left").drop(df2.Id)

```


* Ha az oszlopnév **azonos**:
```python
df1.join(df2, on="Category", how="left")

```



---

### 6. Maximum érték megkeresése DataFrame-ben

Nem aggregációval, hanem a teljes maximális érték kiemelésével:

```python
# 1. Kiszedjük a skalaris értéket head()[0]-al:
max_val = df.select(max(col("Sugars"))).head()[0]

# 2. Rákiértékeljük a szűrést:
df.where(col("Sugars") == max_val).select("Item", "Sugars")

```

---

### 7. Rendezés RDD-ben és DataFrame-ben

* **RDD:** `sortBy(lambda x: x[1], False)` $\rightarrow$ `x[1]` a darabszám/érték, `False` = csökkenő.
* **DataFrame:** `.orderBy(col("oszlop").desc())` vagy `.sort(desc("oszlop"))`.

---

### 8. Fájlbeolvasás és Kiírás HDFS útvonalai

* **Mindig figyelj az útvonalra:** `hdfs://namenode:8020/...`

```python
# Beolvasás fejléccel és típusfelismeréssel
df = spark.read.option("header", True) \
               .option("inferSchema", True) \
               .csv("hdfs://namenode:8020/data/raw/menu.csv")

# Kiírás 1etlen fájlba:
df.coalesce(1).write.mode("overwrite").option("header", True).csv(...)

```

---

### 9. Python alapok szűréshez (String műveletek RDD-ben)

* Kisbetűssé alakítás: `.lower()`
* Szóközök levágása: `.strip()`
* Dátum kinyerése ISO timestampből: `"2026-09-04T12:00:00".split("T")[0]` $\rightarrow$ `"2026-09-04"`

---

### 10. Mentális csekklista a feladat indításakor

1. **Ne futtasd újra** a `sc = SparkContext(...)` cellát, ha már létezik a környezet! (Restart Kernel, ha hiba van).
2. Nézd meg, mit kér a kimenet: `.collect()`, `.take(3)`, vagy `.show(20, False)` (ez utóbbi nem vágja le a hosszú szövegeket).
3. Ne felejtsd el az `.alias()` használatát az elvárt oszlopnevekhez ( pl. `[Name, Cnt]` ).

Sok sikert a vizsgához! 🚀