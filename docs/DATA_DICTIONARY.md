# Data Dictionary

**Raw file:** `data/raw/SuperStore_Sales_Dataset.csv` (5,901 rows)
**Cleaned file:** `data/processed/superstore_clean.csv` (produced by `analysis/sales_analysis.py`)
**Grain:** one row = one product line within an order.

| Column | Type | Description |
|--------|------|-------------|
| Row ID | Integer | Row number from the source system. Not fully unique (ID 4918 appears twice), so not used as a key. |
| Order ID | Text | Order identifier, e.g. `CA-2019-160304`. 3,003 unique orders. |
| Order Date | Date | Date the order was placed (day/month/year in the raw file). |
| Ship Date | Date | Date the order was shipped. |
| Ship Mode | Text | Standard Class, Second Class, First Class, Same Day. |
| Customer ID | Text | Customer identifier. 773 unique customers. |
| Customer Name | Text | Customer name. |
| Segment | Text | Consumer, Corporate, Home Office. |
| Country | Text | Always United States. |
| City | Text | Delivery city. |
| State | Text | Delivery state (49 states). |
| Region | Text | Central, East, South, West. |
| Product ID | Text | Product identifier. |
| Category | Text | Furniture, Office Supplies, Technology. |
| Sub-Category | Text | 17 sub-categories (e.g. Phones, Chairs, Binders). |
| Product Name | Text | Full product description. |
| Sales | Decimal | Revenue for the line, in US dollars. |
| Quantity | Integer | Units sold. |
| Profit | Decimal | Profit for the line (negative = loss). |
| Returns | Decimal | `1` if the line was returned, blank otherwise. |
| Payment Mode | Text | COD (cash on delivery), Online, Cards. |
| ind1, ind2 | Empty | Empty helper columns; removed during cleaning. |

## Fields added during preparation

| Column | Description |
|--------|-------------|
| Returned | 0/1 flag created from `Returns`. |
| Ship Days | `Ship Date − Order Date` in days (basis of the Power BI `AvgShipDay` field). |
| Year, Month, Month Name, Quarter | Taken from `Order Date`. |
| Profit Margin % | `Profit ÷ Sales × 100` for each line. |
| Loss Making | 1 if `Profit < 0`. |
