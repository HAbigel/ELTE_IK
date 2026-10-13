# Apache Kafka és Spark Streaming (RDD Mikrobatch vs. Natív Streaming)

A gyakorlat célja az **Apache Kafka** mint elosztott üzenetsor bevezetése és az ebből érkező valós idejű adatfolyamok (logok, szenzorok, tweetek, koordináták) feldolgozása Spark segítségével. Minden feladatra **kétféle architektúrájú megoldást** készítünk:

1. **RDD-alapú mikrobatch megoldás:** Structured Streaming olvassa a Kafkát, a `.foreachBatch()` elkapja a mikrobatch DataFrame-et, majd az `.rdd` hívással RDD-vé alakítjuk.
2. **Natív Structured Streaming megoldás:** Deklaratív DataFrame transzformációk, ablakos aggregációk, event-time watermark és `.writeStream`.

> **Fontos architektúrális alapelv:** Nem használjuk a legacy DStream API-t. Az RDD-s megközelítés is Structured Streaming alapú mikrobatch feldolgozás.

---

## 1. Kafka Alapfogalmak és Környezet Előkészítése

| Fogalom | Szerep és Leírás |
| --- | --- |
| **Broker** | A Kafka szerver, amely tárolja és kiszolgálja az üzeneteket/eseményeket. |
| **Topic** | Logikai eseményfolyam (pl. `logs`, `sensors`, `tweets`, `coordinates`). |
| **Partition** | A topic párhuzamosítható, sorrendhelyes naplórészlete. |
| **Offset** | Egyedi, növekvő azonosító a rekord pozíciójára a partíción belül. |
| **Consumer Group** | Fogyasztók csoportja, amely megosztja a partíciók olvasását. |

1. **Kafka Topicok Létrehozása:** PowerShell / CMD.
Hozd létre a 4 szükséges topicot 3 partícióval:

```powershell
docker compose exec kafka /opt/kafka/bin/kafka-topics.sh --bootstrap-server kafka:9092 --create --if-not-exists --topic logs --partitions 3 --replication-factor 1
docker compose exec kafka /opt/kafka/bin/kafka-topics.sh --bootstrap-server kafka:9092 --create --if-not-exists --topic sensors --partitions 3 --replication-factor 1
docker compose exec kafka /opt/kafka/bin/kafka-topics.sh --bootstrap-server kafka:9092 --create --if-not-exists --topic tweets --partitions 3 --replication-factor 1
docker compose exec kafka /opt/kafka/bin/kafka-topics.sh --bootstrap-server kafka:9092 --create --if-not-exists --topic coordinates --partitions 3 --replication-factor 1

```


2. **SparkSession és Kafka Beolvasó Kód:** Jupyter Notebook.
```python
from pyspark.sql import SparkSession
import pyspark.sql.functions as F
import pyspark.sql.types as T

spark = (SparkSession.builder
         .appName("BigDataKafkaGyak")
         .config("spark.jars.packages", "org.apache.spark:spark-sql-kafka-0-10_2.13:4.0.1")
         .getOrCreate())

spark.sparkContext.setLogLevel("WARN")
KAFKA_BOOTSTRAP = "kafka:9092"

def json_stream(topic, schema):
    raw = (spark.readStream
           .format("kafka")
           .option("kafka.bootstrap.servers", KAFKA_BOOTSTRAP)
           .option("subscribe", topic)
           .option("startingOffsets", "latest")
           .load())
    
    # A Kafka value bináris, stringgé konvertáljuk és JSON sémára illesztjük
    return (raw.select(F.from_json(F.col("value").cast("string"), schema).alias("data"))
               .select("data.*"))

```


3. **Sémák Definíciója:** Jupyter Notebook.
```python
log_schema = T.StructType([
    T.StructField("timestamp", T.StringType()),
    T.StructField("srcip", T.StringType()),
    T.StructField("dstip", T.StringType()),
    T.StructField("method", T.StringType()),
    T.StructField("url", T.StringType()),
    T.StructField("status", T.IntegerType())
])

sensor_schema = T.StructType([
    T.StructField("sensor_id", T.StringType()),
    T.StructField("timestamp", T.StringType()),
    T.StructField("type", T.StringType()),
    T.StructField("value", T.DoubleType())
])

tweet_schema = T.StructType([
    T.StructField("user", T.StringType()),
    T.StructField("timestamp", T.StringType()),
    T.StructField("text", T.StringType()),
    T.StructField("hashtag", T.StringType())
])

coordinate_schema = T.StructType([
    T.StructField("phone_id", T.StringType()),
    T.StructField("timestamp", T.StringType()),
    T.StructField("lat", T.DoubleType()),
    T.StructField("lon", T.DoubleType())
])

```


---

## 2. A Nyolc Gyakorlati Feladat Megoldása

---

### Feladat 1: URL-statisztika (`logs` topic)

**Cél:** Meghatározni a legtöbbször lekért URL-eket.

#### RDD-alapú mikrobatch megoldás

```python
def process_urls_rdd(batch_df, batch_id):
    if batch_df.isEmpty():
        return
    rdd = batch_df.rdd
    top_urls = (rdd.map(lambda r: (r.url, 1))
                   .reduceByKey(lambda a, b: a + b)
                   .sortBy(lambda x: x[1], ascending=False)
                   .take(5))
    print(f"--- Batch {batch_id} Top URLs (RDD) ---")
    for url, count in top_urls:
        print(f"{url}: {count}")

q1_rdd = json_stream("logs", log_schema).writeStream.foreachBatch(process_urls_rdd).start()

```

#### Natív Structured Streaming megoldás

```python
logs_df = json_stream("logs", log_schema)
url_counts = logs_df.groupBy("url").count().orderBy(F.col("count").desc()).limit(5)

q1_stream = (url_counts.writeStream
             .format("console")
             .outputMode("complete")
             .start())

```

---

### Feladat 2: Támadásdetektálás (`logs` topic)

**Cél:** Detektálni, ha 30 másodperces ablakban egy `srcip` legalább 5 különböző `dstip`-et céloz meg.

#### RDD-alapú mikrobatch megoldás (Mikrobatch szintű közelítés)

```python
def detect_attacks_rdd(batch_df, batch_id):
    if batch_df.isEmpty():
        return
    rdd = batch_df.rdd
    # (srcip, dstip) párok vétele -> distinct -> (srcip, 1) -> aggregáció
    attacks = (rdd.map(lambda r: (r.srcip, r.dstip))
                  .distinct()
                  .map(lambda x: (x[0], 1))
                  .reduceByKey(lambda a, b: a + b)
                  .filter(lambda x: x[1] >= 5)
                  .collect())
    if attacks:
        print(f" ALERT Batch {batch_id} Attackers:", attacks)

q2_rdd = json_stream("logs", log_schema).writeStream.foreachBatch(detect_attacks_rdd).start()

```

#### Natív Structured Streaming megoldás

```python
logs_df = json_stream("logs", log_schema) \
    .withColumn("event_time", F.to_timestamp("timestamp"))

attacks_stream = (
    logs_df
    .withWatermark("event_time", "10 seconds")
    .groupBy(F.window("event_time", "30 seconds", "5 seconds"), "srcip")
    .agg(F.countDistinct("dstip").alias("unique_targets"))
    .filter("unique_targets >= 5")
)

q2_stream = (attacks_stream.writeStream
             .format("console")
             .outputMode("update")
             .start())

```

---

### Feladat 3: Szenzorstatisztika (`sensors` topic)

**Cél:** Szenzoronként átlag, min, max és mérésszám kiszámítása.

#### RDD-alapú mikrobatch megoldás

```python
def process_sensors_rdd(batch_df, batch_id):
    if batch_df.isEmpty():
        return
    rdd = batch_df.rdd
    # Key: sensor_id, Value: (value, min, max, 1)
    stats = (rdd.map(lambda r: (r.sensor_id, (r.value, r.value, r.value, 1)))
                .reduceByKey(lambda a, b: (
                    a[0] + b[0],           # sum
                    min(a[1], b[1]),       # min
                    max(a[2], b[2]),       # max
                    a[3] + b[3]            # count
                ))
                .mapValues(lambda x: (round(x[0]/x[3], 2), x[1], x[2], x[3]))
                .collect())
    print(f"--- Batch {batch_id} Sensor Stats [Avg, Min, Max, Count] ---", stats)

q3_rdd = json_stream("sensors", sensor_schema).writeStream.foreachBatch(process_sensors_rdd).start()

```

#### Natív Structured Streaming megoldás (1 perces ablak)

```python
sensors_df = json_stream("sensors", sensor_schema) \
    .withColumn("event_time", F.to_timestamp("timestamp"))

sensor_stats_stream = (
    sensors_df
    .withWatermark("event_time", "10 seconds")
    .groupBy(F.window("event_time", "1 minute"), "sensor_id")
    .agg(
        F.avg("value").alias("avg_val"),
        F.min("value").alias("min_val"),
        F.max("value").alias("max_val"),
        F.count("value").alias("cnt")
    )
)

q3_stream = (sensor_stats_stream.writeStream
             .format("console")
             .outputMode("update")
             .start())

```

---

### Feladat 4: Tűzriasztás (`sensors` topic)

**Cél:** Riasztás, ha egy hőmérséklet-szenzor 30 másodperces ablakban legalább 3 alkalommal 80 °C feletti értéket mér.

#### RDD-alapú mikrobatch megoldás

```python
def fire_alarm_rdd(batch_df, batch_id):
    if batch_df.isEmpty():
        return
    rdd = batch_df.rdd
    alarms = (rdd.filter(lambda r: r.type == "temperature" and r.value >= 80.0)
                 .map(lambda r: (r.sensor_id, 1))
                 .reduceByKey(lambda a, b: a + b)
                 .filter(lambda x: x[1] >= 3)
                 .collect())
    if alarms:
        print(f" FIRE ALARM Batch {batch_id}:", alarms)

q4_rdd = json_stream("sensors", sensor_schema).writeStream.foreachBatch(fire_alarm_rdd).start()

```

#### Natív Structured Streaming megoldás

```python
fire_stream = (
    json_stream("sensors", sensor_schema)
    .withColumn("event_time", F.to_timestamp("timestamp"))
    .filter(F.col("type") == "temperature")
    .withWatermark("event_time", "10 seconds")
    .groupBy(F.window("event_time", "30 seconds", "10 seconds"), "sensor_id")
    .agg(F.sum(F.when(F.col("value") >= 80.0, 1).otherwise(0)).alias("high_temp_cnt"))
    .filter("high_temp_cnt >= 3")
)

q4_stream = (fire_stream.writeStream
             .format("console")
             .outputMode("update")
             .start())

```

---

### Feladat 5: Hashtag-elemzés (`tweets` topic)

**Cél:** A leggyakoribb hashtagek meghatározása.

#### RDD-alapú mikrobatch megoldás

```python
def process_hashtags_rdd(batch_df, batch_id):
    if batch_df.isEmpty():
        return
    rdd = batch_df.rdd
    top_hashtags = (rdd.filter(lambda r: r.hashtag is not None)
                       .map(lambda r: (r.hashtag, 1))
                       .reduceByKey(lambda a, b: a + b)
                       .sortBy(lambda x: x[1], ascending=False)
                       .take(5))
    print(f"--- Batch {batch_id} Top Hashtags ---", top_hashtags)

q5_rdd = json_stream("tweets", tweet_schema).writeStream.foreachBatch(process_hashtags_rdd).start()

```

#### Natív Structured Streaming megoldás

```python
tweets_df = json_stream("tweets", tweet_schema) \
    .withColumn("event_time", F.to_timestamp("timestamp"))

hashtag_stream = (
    tweets_df
    .withWatermark("event_time", "10 seconds")
    .groupBy(F.window("event_time", "1 minute", "10 seconds"), "hashtag")
    .count()
    .orderBy(F.col("count").desc())
    .limit(5)
)

q5_stream = (hashtag_stream.writeStream
             .format("console")
             .outputMode("complete")
             .start())

```

---

### Feladat 6: Hangulatelemzés (`tweets` topic)

**Cél:** Lexikonalapú hangulatértékelés (pozitív: +1, negatív: -1).

```python
positive_words = {"love", "great", "amazing", "happy", "good", "excellent"}
negative_words = {"bad", "terrible", "slow", "hate", "failed", "awful"}

```

#### RDD-alapú mikrobatch megoldás

```python
def analyze_sentiment_rdd(batch_df, batch_id):
    if batch_df.isEmpty():
        return
    
    def score_text(text):
        if not text: return 0
        words = text.lower().split()
        pos = sum(1 for w in words if w in positive_words)
        neg = sum(1 for w in words if w in negative_words)
        return pos - neg

    rdd = batch_df.rdd
    scores = rdd.map(lambda r: score_text(r.text)).collect()
    if scores:
        avg_score = sum(scores) / len(scores)
        print(f"--- Batch {batch_id} Avg Sentiment: {round(avg_score, 3)} ---")

q6_rdd = json_stream("tweets", tweet_schema).writeStream.foreachBatch(analyze_sentiment_rdd).start()

```

#### Natív Structured Streaming megoldás

```python
tweets_df = json_stream("tweets", tweet_schema)

sentiment_stream = (
    tweets_df
    .select(F.explode(F.split(F.lower("text"), " ")).alias("word"))
    .withColumn("score", 
        F.when(F.col("word").isin(list(positive_words)), 1)
         .when(F.col("word").isin(list(negative_words)), -1)
         .otherwise(0)
    )
    .filter("score != 0")
    .groupBy()
    .agg(F.avg("score").alias("avg_sentiment"))
)

q6_stream = (sentiment_stream.writeStream
             .format("console")
             .outputMode("complete")
             .start())

```

---

### Feladat 7: Térbeli cellák (`coordinates` topic)

**Cél:** Koordináták rácscellákra osztása ($0.01^\circ$ kerekítéssel) és az egyedi telefonok megszámlálása cellánként.

#### RDD-alapú mikrobatch megoldás

```python
def process_grid_rdd(batch_df, batch_id):
    if batch_df.isEmpty():
        return
    rdd = batch_df.rdd
    # Grid cella: (round(lat, 2), round(lon, 2))
    grid_counts = (rdd.map(lambda r: ((round(r.lat, 2), round(r.lon, 2)), r.phone_id))
                      .distinct()
                      .map(lambda x: (x[0], 1))
                      .reduceByKey(lambda a, b: a + b)
                      .collect())
    print(f"--- Batch {batch_id} Grid Cell Phone Counts ---", grid_counts)

q7_rdd = json_stream("coordinates", coordinate_schema).writeStream.foreachBatch(process_grid_rdd).start()

```

#### Natív Structured Streaming megoldás

```python
coords_df = json_stream("coordinates", coordinate_schema) \
    .withColumn("event_time", F.to_timestamp("timestamp"))

grid_stream = (
    coords_df
    .withColumn("lat_grid", F.round("lat", 2))
    .withColumn("lon_grid", F.round("lon", 2))
    .withWatermark("event_time", "10 seconds")
    .groupBy(F.window("event_time", "30 seconds"), "lat_grid", "lon_grid")
    .agg(F.countDistinct("phone_id").alias("unique_phones"))
)

q7_stream = (grid_stream.writeStream
             .format("console")
             .outputMode("update")
             .start())

```

---

### Feladat 8: Antennaelemzés (`coordinates` topic + Broadcast)

**Cél:** Mérésként megkeresni a legközelebbi cellaantennát broadcast referenciaadat segítségével.

```python
# Antenna referenciaséma és broadcast előkészítés
antenna_schema = T.StructType([
    T.StructField("antenna_id", T.StringType()),
    T.StructField("lat", T.DoubleType()),
    T.StructField("lon", T.DoubleType())
])

antennas = spark.createDataFrame([
    ("A1", 47.49790, 19.04020),
    ("A2", 47.50100, 19.05500),
    ("A3", 47.49200, 19.05000),
    ("A4", 47.50500, 19.03000)
], antenna_schema)

# Driver oldali lista a broadcast-hoz
antenna_list = [r.asDict() for r in antennas.collect()]
bc_antennas = spark.sparkContext.broadcast(antenna_list)

```

#### RDD-alapú mikrobatch megoldás

```python
def process_antennas_rdd(batch_df, batch_id):
    if batch_df.isEmpty():
        return
    
    local_antennas = bc_antennas.value

    def find_nearest(lat, lon):
        best_ant = None
        min_dist = float("inf")
        for a in local_antennas:
            dist = (lat - a["lat"])**2 + (lon - a["lon"])**2
            if dist < min_dist:
                min_dist = dist
                best_ant = a["antenna_id"]
        return best_ant

    rdd = batch_df.rdd
    nearest_rdd = rdd.map(lambda r: (r.phone_id, find_nearest(r.lat, r.lon))).take(5)
    print(f"--- Batch {batch_id} Nearest Antennas (RDD) ---", nearest_rdd)

q8_rdd = json_stream("coordinates", coordinate_schema).writeStream.foreachBatch(process_antennas_rdd).start()

```

#### Natív Structured Streaming megoldás

```python
coords_df = json_stream("coordinates", coordinate_schema) \
    .withColumn("event_time", F.to_timestamp("timestamp"))

ant_bc_df = F.broadcast(antennas)

nearest_stream = (
    coords_df.alias("c")
    .crossJoin(ant_bc_df.alias("a"))
    .withColumn("dist2", F.pow(F.col("c.lat") - F.col("a.lat"), 2) + F.pow(F.col("c.lon") - F.col("a.lon"), 2))
    .withWatermark("event_time", "10 seconds")
    .groupBy(F.window("event_time", "10 seconds"), "c.phone_id")
    .agg(F.min(F.struct("dist2", "a.antenna_id")).alias("min_struct"))
    .select("window", "phone_id", "min_struct.antenna_id", "min_struct.dist2")
)

q8_stream = (nearest_stream.writeStream
             .format("console")
             .outputMode("update")
             .start())

```

---

## 3. Streaming Query-k Életciklus-Kezelése

A folyamatban lévő lekérdezéseket az alábbi parancsokkal kezelheted a Jupyter notebookban:

```python
# Aktív stream-ek lekérdezése
print("Aktív streamek száma:", len(spark.streams.active))
for q in spark.streams.active:
    print(f"ID: {q.id} | Név: {q.name} | Állapot: {q.status['message']}")

# Egy adott lekérdezés leállítása
q1_stream.stop()

# ÖSSZES aktív lekérdezés leállítása
for q in spark.streams.active:
    q.stop()

```