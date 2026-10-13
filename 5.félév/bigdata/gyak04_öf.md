# Spark Structured Streaming Gyakorlati Útmutató

A gyakorlat célja a valós idejű adatáramok (streaming) feldolgozásának megismerése az **Apache Spark Structured Streaming** segítségével, bemutatva a socket alapú adatforrásokat, a fix és csúszó időablakokat, az **Output Mode**-okat, az **Event Time** és **Watermark** kezelését, a **Broadcast Join** mechanizmust, valamint a gyakorlati komplex feladatok megoldásait.

---

## 1. Architektúra és Technológiai Összehasonlítás

> **Fontos szakmai váltás:** A korábbi **DStream (Spark Streaming)** API mára örökség (legacy) státuszú, új fejlesztések nem érkeznek hozzá. Modern streaming csővezetékekhez a **Spark Structured Streaming** (DataFrame / SQL alapú streaming motor) az iparági standard.

| Szempont | Legacy DStream (Spark Streaming) | Structured Streaming |
| --- | --- | --- |
| **Alapvető Absztrakció** | DStream (Discretized Stream - RDD-k sorozata) | Streaming DataFrame / Dataset |
| **Feldolgozási Modell** | Micro-batch | Micro-batch és Low-Latency Continuous Processing |
| **Időkezelés** | Processing Time (mikor érkezett a node-ra) | **Event Time** (az esemény tényleges keletkezési ideje) |
| **Késve érkező adatok** | Nehezen kezelhető | **Watermark** segítségével automatikusan kezelt |
| **Integráció** | Különálló API | Teljesen egységes a batch DataFrame/SQL API-val |

---

## 2. Adatforrások és Socket Streaming Előkészítése

A gyakorlat során a streaming adatokat Python socket generátorok biztosítják az alábbi portokon:

| Port | Adatforrás | Rekord Struktúrája | Indító Parancs |
| --- | --- | --- | --- |
| **`9001`** | **Szerverlog** | `srcip dstip GET URL` | `python stream_generator.py --port 9001 --rate 5` |
| **`9002`** | **Szenzor** | `sensor_id timestamp type value` | `python stream_generator.py --port 9002 --rate 2` |
| **`9003`** | **Tweet** | `user timestamp text hashtag` | `python stream_generator.py --port 9003 --rate 3` |
| **`9004`** | **Telefon** | `phone_id timestamp lat lon` | `python stream_generator.py --port 9004 --rate 4` |

### Streaming DataFrame Létrehozása Socketből

```python
import pyspark.sql.functions as F
import pyspark.sql.types as T
from pyspark.sql import SparkSession

spark = SparkSession.builder.appName("BigDataGyakStream").getOrCreate()

def socket_stream(port):
    return (spark.readStream.format("socket")
            .option("host", "sensorStream")
            .option("port", port)
            .load())

```

---

## 3. Időablakok és Output Mode-ok

### Időablakok Típusai

1. **Fix (Tumbling) Ablak:** Egymást nem fedő, fix időtartamú ablakok (pl. 10 perces blokkok).
2. **Csúszó (Sliding) Ablak:** Egymást átfedő ablakok, amelyek meghatározott időközönként csúsznak el (pl. 10 perces ablakok 5 percenként kiértékelve).

```python
# 1. Fix ablak (Tumbling Window)
df_tumbling = df.groupBy(
    F.window(F.col("ingest_time"), "10 minutes"), "urls"
).count()

# 2. Csúszó ablak (Sliding Window)
df_sliding = df.groupBy(
    F.window(F.col("ingest_time"), "10 minutes", "5 minutes"), "urls"
).count()

```

### Output Mode-ok Működése

| Mode | Jelentés | Használati Eset |
| --- | --- | --- |
| **`append`** | **Csak az új, végleges sormódosításokat** írja ki, amelyek már biztosan nem változnak (Watermark szükséges aggregáció esetén). | Nem aggregált szűrések, vagy lezárt ablakos aggregációk. |
| **`update`** | **Csak azokat a sorokat írja ki**, amelyek az adott trigger alatt megváltoztak vagy újonnan jöttek létre. | Folyamatosan frissülő dashboardok, riasztások. |
| **`complete`** | **A teljes eredménytáblát kiírja** minden egyes trigger lefutásakor. | Globális aggregációk, Top-N lekérdezések. |

---

## 4. Haladó Streaming Koncepciók

### Event Time & Watermark

A **Watermark** határozza meg, hogy a Spark mennyi ideig tartsa nyitva az aggregációs állapotot (state) a késve érkező adatok számára.

```python
df.withWatermark("event_time", "10 seconds") \
  .groupBy(F.window("event_time", "20 seconds", "5 seconds"), "phone_id")

```

* **Szerepe:** Megakadályozza az in-memory állapot korlátlan növekedését és a memória kimerülését (OOM).
* **Szabály:** Ha egy esemény $EventTime < MaxEventTime - WatermarkDelay$, a rendszer figyelmen kívül hagyja (eldobja).

### Broadcast Join referenciaadatokkal

Streaming adatok és egy kicsi, statikus referenciaadat (pl. antenna koordináták) összekapcsolásakor a **Broadcast Join** megelőzi a drága hálózati adatmozgatást (shuffle).

```python
# antennas = kis statikus DataFrame
antennas_bc = F.broadcast(antennas).alias("a")
coords_stream = coords.alias("c")

# CrossJoin Broadcast-olt adathalmazzal
ca = coords_stream.crossJoin(antennas_bc)

```

---

## 5. Önálló Feladatok Megoldása

### 1. Leggyakoribb Hashtag-ek (Tweet Stream, Port 9003)

**Feladat:** Készíts csúszó ablakos aggregációt, és jelenítsd meg a Top 5 hashtaget!

```python
tweets_df = socket_stream(9003)

top_hashtags = (
    tweets_df
    .select(F.split("value", " ").alias("p"))
    .where(F.size("p") >= 4)
    .select(
        F.to_timestamp(F.col("p")[1]).alias("event_time"),
        F.col("p")[3].alias("hashtag")
    )
    .withWatermark("event_time", "10 seconds")
    .groupBy(
        F.window("event_time", "1 minute", "10 seconds"),
        "hashtag"
    )
    .count()
    .orderBy(F.col("count").desc())
    .limit(5)
)

query1 = (
    top_hashtags.writeStream
    .format("console")
    .outputMode("complete")
    .option("truncate", "false")
    .start()
)

```

---

### 2. Twitter Word Count Stopword Szűréssel (Port 9003)

**Feladat:** Bontsd szavakra a tweetek szövegét, távolítsd el a gyakori stopwordöket, és jelenítsd meg a Top 10 szót!

```python
stopwords = ["is", "a", "the", "in", "on", "at", "to", "for", "and", "or", "of", "with"]

words_df = (
    tweets_df
    .select(F.split("value", " ").alias("p"))
    .where(F.size("p") >= 3)
    .select(
        F.to_timestamp(F.col("p")[1]).alias("event_time"),
        F.explode(F.split(F.lower(F.col("p")[2]), " ")).alias("word")
    )
    .filter(~F.col("word").isin(stopwords) & (F.length("word") > 2))
    .withWatermark("event_time", "10 seconds")
    .groupBy(
        F.window("event_time", "30 seconds", "10 seconds"),
        "word"
    )
    .count()
    .orderBy(F.col("count").desc())
    .limit(10)
)

query2 = (
    words_df.writeStream
    .format("console")
    .outputMode("complete")
    .start()
)

```

---

### 3. Twitter Hangulatelemzés (Sentiment Analysis)

**Feladat:** Készíts lexikonalapú hangulatelemzést (+1 poz, -1 neg), és számítsd ki az átlagos megítélést a `#GameLaunch` hashtagra!

```python
# Pozitív és negatív szavak leképezése Spark SQL kifejezéssel
tweets_parsed = (
    tweets_df
    .select(F.split("value", " ").alias("p"))
    .where(F.size("p") >= 4)
    .select(
        F.to_timestamp(F.col("p")[1]).alias("event_time"),
        F.lower(F.col("p")[2]).alias("text"),
        F.col("p")[3].alias("hashtag")
    )
    .filter(F.col("hashtag") == "#GameLaunch")
    .select(
        "event_time",
        F.explode(F.split(F.col("text"), " ")).alias("word")
    )
    .withColumn("sentiment", 
        F.when(F.col("word").isin(["love", "great", "amazing", "happy", "good", "excellent"]), 1)
         .when(F.col("word").isin(["bad", "terrible", "slow", "hate", "failed", "awful"]), -1)
         .otherwise(0)
    )
    .filter(F.col("sentiment") != 0)
)

sentiment_avg = (
    tweets_parsed
    .withWatermark("event_time", "10 seconds")
    .groupBy(F.window("event_time", "1 minute", "10 seconds"))
    .agg(
        F.avg("sentiment").alias("avg_sentiment"),
        F.count("sentiment").alias("word_count")
    )
)

query3 = (
    sentiment_avg.writeStream
    .format("console")
    .outputMode("complete")
    .start()
)

```

---

### 4. Támadásdetektálás 1: Egy IP-ről sok címet céloznak (Port 9001)

**Feladat:** Detektáld, ha egy `srcip` 30 másodperces ablakban legalább 5 különböző `dstip`-re küld kérést!

```python
logs_df = socket_stream(9001)

attack_1 = (
    logs_df
    .select(F.split("value", " ").alias("p"))
    .where(F.size("p") >= 4)
    .select(
        F.current_timestamp().alias("ingest_time"),
        F.col("p")[0].alias("srcip"),
        F.col("p")[1].alias("dstip")
    )
    .withWatermark("ingest_time", "10 seconds")
    .groupBy(
        F.window("ingest_time", "30 seconds", "5 seconds"),
        "srcip"
    )
    .agg(F.countDistinct("dstip").alias("unique_dst_ips"))
    .filter(F.col("unique_dst_ips") >= 5)
)

query4 = (
    attack_1.writeStream
    .format("console")
    .outputMode("update")
    .start()
)

```

---

### 5. Támadásdetektálás 2: Sok címről egy IP-t támadnak (DDoS szimuláció)

**Feladat:** Detektáld, ha 30 másodperces ablakban legalább 5 különböző `srcip` ugyanazt a `dstip`-et célozza!

```python
attack_2 = (
    logs_df
    .select(F.split("value", " ").alias("p"))
    .where(F.size("p") >= 4)
    .select(
        F.current_timestamp().alias("ingest_time"),
        F.col("p")[0].alias("srcip"),
        F.col("p")[1].alias("dstip")
    )
    .withWatermark("ingest_time", "10 seconds")
    .groupBy(
        F.window("ingest_time", "30 seconds", "5 seconds"),
        "dstip"
    )
    .agg(F.countDistinct("srcip").alias("unique_src_ips"))
    .filter(F.col("unique_src_ips") >= 5)
)

query5 = (
    attack_2.writeStream
    .format("console")
    .outputMode("update")
    .start()
)

```