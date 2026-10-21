# Adatbázisok II. - Practical Cheatsheet & Quick Reference

---

## 1. Oracle Catalog Views & Meta-Tables Quick Reference

### Data Dictionary Hierarchy
* `USER_*`: Objects owned by the current user.
* `ALL_*`: Objects accessible to the current user.
* `DBA_*`: All database objects (requires privileges; falls back to `ALL_*`/`USER_*`).

> **Golden Rule for Strings:** Catalog identifiers are stored in **UPPERCASE** by default. Use `UPPER(p_input)` for procedure parameters.

### Key Catalog Tables & Columns

| View | Key Columns | Purpose / Common Uses |
| :--- | :--- | :--- |
| `DBA_OBJECTS` | `OWNER`, `OBJECT_NAME`, `OBJECT_TYPE`, `CREATED`, `DATA_OBJECT_ID` | Check object existence, creation dates, object types (`TABLE`, `VIEW`, `INDEX`, `TRIGGER`). |
| `DBA_TAB_COLUMNS` | `OWNER`, `TABLE_NAME`, `COLUMN_NAME`, `COLUMN_ID`, `DATA_TYPE` | Inspect table/view schema, data types, column positions. |
| `DBA_TABLES` | `OWNER`, `TABLE_NAME`, `TABLESPACE_NAME`, `IOT_TYPE`, `CLUSTER_NAME`, `PARTITIONED` | Table metadata, check if table is IOT, Clustered, or Partitioned. |
| `DBA_INDEXES` | `OWNER`, `INDEX_NAME`, `TABLE_OWNER`, `TABLE_NAME`, `INDEX_TYPE`, `UNIQUENESS` | Index properties (`NORMAL`, `BITMAP`, `IOT - TOP`). |
| `DBA_IND_COLUMNS` | `INDEX_OWNER`, `INDEX_NAME`, `COLUMN_NAME`, `COLUMN_POSITION`, `DESCEND` | Indexed columns and sort direction (`ASC`/`DESC`). |
| `DBA_IND_EXPRESSIONS` | `INDEX_OWNER`, `INDEX_NAME`, `COLUMN_EXPRESSION`, `COLUMN_POSITION` | Function-based index expressions. |
| `DBA_SEGMENTS` | `OWNER`, `SEGMENT_NAME`, `SEGMENT_TYPE`, `BYTES`, `BLOCKS`, `EXTENTS` | Physical storage footprint by object segment. |
| `DBA_EXTENTS` | `OWNER`, `SEGMENT_NAME`, `PARTITION_NAME`, `FILE_ID`, `BLOCK_ID`, `BYTES`, `BLOCKS` | Extent allocations and physical file mapping. |
| `DBA_DATA_FILES` / `DBA_TEMP_FILES` | `FILE_NAME`, `FILE_ID`, `TABLESPACE_NAME`, `BYTES`, `BLOCKS` | Datafile sizes and mapping to tablespaces. |
| `DBA_FREE_SPACE` | `TABLESPACE_NAME`, `FILE_ID`, `BLOCK_ID`, `BYTES`, `BLOCKS` | Unallocated space in datafiles. |
| `DBA_PART_TABLES` | `OWNER`, `TABLE_NAME`, `PARTITIONING_TYPE`, `SUBPARTITIONING_TYPE` | High-level partitioning strategy (`RANGE`, `HASH`, `LIST`). |
| `DBA_TAB_PARTITIONS` | `TABLE_OWNER`, `TABLE_NAME`, `PARTITION_NAME`, `HIGH_VALUE`, `PARTITION_POSITION` | Partition boundaries and positions. |

---

## 2. Essential SQL Catalog Patterns

### Filter Users with Multiple Specific Objects
```sql
-- Users with both VIEWs and TRIGGERs
SELECT owner
FROM dba_objects
GROUP BY owner
HAVING SUM(CASE WHEN object_type = 'TRIGGER' THEN 1 ELSE 0 END) > 0
   AND SUM(CASE WHEN object_type = 'VIEW' THEN 1 ELSE 0 END) > 0;
```

### Table Column Constraints Verification
```sql
-- Tables having BOTH column 1 and column 4 as VARCHAR2
SELECT owner, table_name
FROM dba_tab_columns
WHERE column_id IN (1, 4) AND data_type = 'VARCHAR2'
GROUP BY owner, table_name
HAVING COUNT(DISTINCT column_id) = 2;
```

### Physical Storage & Extent Allocation Queries
```sql
-- Size of non-partitioned tables (Top 1)
SELECT owner, segment_name, bytes, extents
FROM (
    SELECT owner, segment_name, bytes, extents
    FROM dba_segments
    WHERE segment_type = 'TABLE'
    ORDER BY bytes DESC
)
WHERE ROWNUM = 1;

-- Total Tablespace sizes (Datafiles + Tempfiles)
WITH df AS (
    SELECT tablespace_name, COUNT(*) AS cnt, SUM(bytes) AS bytes 
    FROM dba_data_files GROUP BY tablespace_name
), tf AS (
    SELECT tablespace_name, COUNT(*) AS cnt, SUM(bytes) AS bytes 
    FROM dba_temp_files GROUP BY tablespace_name
)
SELECT t.tablespace_name,
       NVL(df.cnt, 0) + NVL(tf.cnt, 0) AS file_count,
       NVL(df.bytes, 0) + NVL(tf.bytes, 0) AS total_bytes
FROM dba_tablespaces t
LEFT JOIN df ON df.tablespace_name = t.tablespace_name
LEFT JOIN tf ON tf.tablespace_name = t.tablespace_name;
```

---

## 3. ROWID Architecture & Block Analysis

### ROWID Structure (18-character Base64)
```text
OOOOOO FFF BBBBBB RRR
│      │   │      └─ Row Number within block (3 chars)
│      │   └──────── Block Number within datafile (6 chars)
│      └──────────── Relative Datafile Number (3 chars)
└────────────────── Data Object ID (6 chars)
```

### `DBMS_ROWID` Package Cheat Sheet
```sql
DBMS_ROWID.ROWID_OBJECT(rowid)              -- Returns Data Object ID
DBMS_ROWID.ROWID_RELATIVE_FNO(rowid)        -- Returns Relative File Number
DBMS_ROWID.ROWID_BLOCK_NUMBER(rowid)        -- Returns Block Number within File
DBMS_ROWID.ROWID_ROW_NUMBER(rowid)          -- Returns Row Index in Block
DBMS_ROWID.ROWID_TO_ABSOLUTE_FNO(rowid, owner, table_name) -- Absolute File ID
```

### Counting Used vs. Allocated Blocks for a Table
```sql
-- 1. Number of allocated blocks (from storage segments)
SELECT NVL(SUM(blocks), 0) AS allocated_blocks
FROM dba_segments
WHERE owner = 'NIKOVITS' AND segment_name = 'MY_TABLE';

-- 2. Number of non-empty blocks (containing >= 1 row)
SELECT COUNT(DISTINCT DBMS_ROWID.ROWID_BLOCK_NUMBER(rowid)) AS nonempty_blocks
FROM nikovits.my_table;
```

---

## 4. Key PL/SQL Code Templates

### Pattern 1: Table Inspection / Cursor Loop
```sql
CREATE OR REPLACE PROCEDURE list_indexes(p_owner VARCHAR2, p_table VARCHAR2) IS
BEGIN
  FOR r IN (
    SELECT i.index_name, NVL(SUM(s.bytes), 0) AS size_bytes
    FROM dba_indexes i
    LEFT JOIN dba_segments s 
      ON s.owner = i.owner 
     AND s.segment_name = i.index_name
     AND s.segment_type IN ('INDEX', 'INDEX PARTITION', 'INDEX SUBPARTITION')
    WHERE i.table_owner = UPPER(p_owner)
      AND i.table_name = UPPER(p_table)
    GROUP BY i.index_name
    ORDER BY i.index_name
  ) LOOP
    DBMS_OUTPUT.PUT_LINE(r.index_name || ': ' || r.size_bytes || ' bytes');
  END LOOP;
END;
/
```

### Pattern 2: Safe Dynamic SQL Execution
```sql
CREATE OR REPLACE PROCEDURE empty_blocks(p_owner VARCHAR2, p_table VARCHAR2) IS
  v_total_blocks     NUMBER;
  v_nonempty_blocks  NUMBER;
  v_owner            VARCHAR2(128);
  v_table            VARCHAR2(128);
BEGIN
  -- Sanitize inputs to prevent SQL Injection
  v_owner := DBMS_ASSERT.SCHEMA_NAME(UPPER(p_owner));
  v_table := DBMS_ASSERT.SIMPLE_SQL_NAME(UPPER(p_table));

  SELECT NVL(SUM(blocks), 0) INTO v_total_blocks
  FROM dba_segments
  WHERE owner = v_owner AND segment_name = v_table;

  EXECUTE IMMEDIATE 
    'SELECT COUNT(DISTINCT DBMS_ROWID.ROWID_BLOCK_NUMBER(rowid)) ' ||
    'FROM ' || v_owner || '.' || v_table
  INTO v_nonempty_blocks;

  DBMS_OUTPUT.PUT_LINE('Empty Blocks: ' || (v_total_blocks - v_nonempty_blocks));
END;
/
```

---

## 5. Advanced Table Types & Storage Footprints

### Index-Organized Tables (IOT)
* Primary data is stored directly in the Primary Key index structure.
* **Parts**: Top/Primary Index (`INDEX_TYPE LIKE 'IOT%'`), optional Overflow Segment (`IOT_TYPE = 'IOT_OVERFLOW'`).
* **Total Size Calculation**: Must sum bytes of top index segment + overflow segment.

```sql
SELECT s.segment_name, s.segment_type, s.bytes
FROM dba_segments s
WHERE s.owner = 'NIKOVITS'
  AND s.segment_name IN (
      SELECT index_name FROM dba_indexes WHERE table_owner = 'NIKOVITS' AND table_name = 'MY_IOT'
      UNION
      SELECT table_name FROM dba_tables WHERE owner = 'NIKOVITS' AND iot_name = 'MY_IOT'
  );
```

### Partitioned Tables
* Data segments exist at the **Partition** (`TABLE PARTITION`) or **Subpartition** (`TABLE SUBPARTITION`) level.
* The main logical table entry in `DBA_SEGMENTS` does **not** hold size information directly.
* Total size: `SUM(bytes)` from `DBA_SEGMENTS` filtering for `segment_name = 'TABLE_NAME'`.

---

## 6. Query Cost Estimation & Relational Algebra Formulas

### Basic Parameters & Definitions
* $T(R)$: Number of tuples in relation $R$.
* $B(R)$: Number of data blocks in $R = \lceil T(R) / bf(R) \rceil$.
* $bf(R)$: Blocking factor (number of tuples per block).
* $V(R, A)$: Distinct values of attribute $A$ in $R$.
* $M$: Available main memory buffers (in blocks).

---

### Index & B+ Tree Formulas
1. **Unclustered Dense Index**: 1 index entry per record $\Rightarrow B(I) = \lceil T(R) / bf(I) \rceil$.
2. **Sparse Index**: 1 index entry per data block $\Rightarrow B(I) = \lceil B(R) / bf(I) \rceil$.
3. **Effective Block Capacity (with fill factor $p \le 1.0$)**:
   $$bf_{eff} = bf \cdot p$$
4. **B+ Tree Height / IO Cost**:
   $$\text{IO Cost} = \text{Height}(B^+ \text{Tree}) + 1 \quad (\text{if unclustered lookup})$$

---

### Selection & Projection Operations
* **Exact match ($A = x$)**:
  $$T(W) = \frac{T(R)}{V(R, A)}$$
* **Conjunction ($A = x \land B = y$)** [Independent columns]:
  $$T(W) = \frac{T(R)}{V(R, A) \cdot V(R, B)}$$
* **Disjunction ($A = x \lor B = y$)** [Inclusion-Exclusion]:
  $$T(W) = T(A=x) + T(B=y) - T(A=x \land B=y)$$

---

### External Merge Sort Cost
* **Number of initial runs**: $N_0 = \lceil B(R) / M \rceil$
* **Merge fan-out per pass**: $M - 1$
* **Total Passes**: $1 + \lceil \log_{M-1} (N_0) \rceil$
* **Total I/O Cost**:
  $$\text{Total Cost} = 2 \cdot B(R) \cdot \text{Total Passes}$$

---

### Join Operations & Costs

1. **Cross Join ($R \times S$)**:
   * Result Size: $T(W) = T(R) \cdot T(S)$
2. **Natural Join ($R \bowtie_A S$)**:
   * Result Size: 
     $$T(W) = \frac{T(R) \cdot T(S)}{\max(V(R, A), V(S, A))}$$
3. **Block Nested Loop Join** (Outer: $S$, Inner: $R$):
   $$\text{I/O Cost} = B(S) + \left\lceil \frac{B(S)}{M - 2} \right\rceil \cdot B(R)$$
4. **2-Pass Hash Join** (assuming smallest relation fits into partitioned memory):
   $$\text{I/O Cost} = 3 \cdot (B(R) + B(S))$$
5. **Sort-Merge Join**:
   $$\text{I/O Cost} = \text{Cost}(\text{Sort } R) + \text{Cost}(\text{Sort } S) + (B(R) + B(S))$$
6. **Index Join** (Iterate over $S$, lookup in $R$ via index, $R$ unclustered):
   $$\text{I/O Cost} = B(S) + T(S) \cdot \left( \frac{T(R)}{V(R, A)} \right)$$

---

## 7. Common Traps & Exam Pitfalls

1. **Upper/Lower Case Sensitivity**:
   * Catalog string literals must be UPPERCASE: `WHERE owner = 'NIKOVITS'` (Not `'nikovits'`).
2. **`ROWNUM = 1` Placement**:
   * `ROWNUM` filtering happens **before** `ORDER BY` unless wrapped inside a subquery!
   * *Correct Pattern*: `SELECT * FROM (SELECT ... ORDER BY col) WHERE ROWNUM = 1;`
3. **Partitioned Table Size Errors**:
   * Querying `DBA_TABLES.TABLESPACE_NAME` or `DBA_SEGMENTS` directly for a partitioned table often returns `NULL` or incomplete sizes. Always aggregate across `TABLE PARTITION` / `SUBPARTITION` segments.
4. **`COUNT(*)` vs `COUNT(column)` in Outer Joins**:
   * `COUNT(*)` counts empty outer-joined null rows as `1`.
   * `COUNT(column)` correctly yields `0` when the joined row is `NULL`.
5. **Allocated Blocks vs Non-Empty Blocks**:
   * `DBA_SEGMENTS.BLOCKS` shows allocated extent blocks, **not** blocks containing data rows. Use `DBMS_ROWID` to find non-empty blocks.