# SQL Practice Record

### **Topic:** Data Aggregation and Table Joins
### **Date Solved:** 2026-02-01

---

## 1. The Scenario
You are working with two tables: `Customers` and `Orders`.

### **Table: Customers**
| customer_id | name | city |
| :--- | :--- | :--- |
| 1 | Alice Smith | New York |
| 2 | Bob Jones | Chicago |
| 3 | Charlie Brown | New York |
| 4 | Diana Prince | Seattle |

### **Table: Orders**
| order_id | customer_id | order_amount | order_date |
| :--- | :--- | :--- | :--- |
| 101 | 1 | 200.00 | 2023-01-10 |
| 102 | 1 | 150.00 | 2023-01-15 |
| 103 | 2 | 300.00 | 2023-02-01 |
| 104 | 3 | 50.00 | 2023-02-10 |
| 105 | 1 | 100.00 | 2023-03-05 |

---

## 2. The Task
Write a SQL query to find the total amount of money spent by each customer. Return the customer's name and their total spent.

---

## 3. The Solution

```sql
/**
 * TASK: Calculate Total Spending per Customer
 * CONCEPTS: INNER JOIN, SUM(), GROUP BY
 */

SELECT 
  c.name, 
  SUM(o.order_amount) AS total_spent
FROM Orders o
INNER JOIN Customers c 
  ON c.customer_id = o.customer_id
GROUP BY 
  c.customer_id, 
  c.name;
```

### **Technical Implementation Notes**

**1. Grouping Logic (The "Why" & "How")**
* **Why:** Grouping only by `c.name` is dangerous. If two different customers share the same name (e.g., two "Alice Smiths"), the database will merge their financial data into one record, resulting in inaccurate reporting.
* **How:** Included `c.customer_id` in the `GROUP BY` clause. This forces the database to distinguish between unique IDs, even if the display names are identical.

**2. Join Syntax (The "Why" & "How")**
* **Why:** Standard `JOIN` can be ambiguous to future readers (is it `LEFT`? is it `INNER`?).
* **How:** Used `INNER JOIN` to explicitly state the intent: only fetch customers who have actually placed orders, filtering out those with null matches.

**3. Naming Conventions (The "Why" & "How")**
* **Why:** Spaces in column aliases (like `"Total Spent"`) require quote marks and cause syntax errors in downstream applications (Python, Tableau).
* **How:** Used `snake_case` (`total_spent`) to ensure compatibility and cleaner syntax reference.