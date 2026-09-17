PROCUREMENT_COLLECTION = "procurement_records"


PROCUREMENT_SCHEMA = """
MongoDB collection: procurement_records

Each document represents ONE PROCUREMENT LINE RECORD.
A document does NOT necessarily represent one purchase order.

Important business rules:

1. Unique purchase order:
   Use the `order_key` field.

2. Number of orders:
   Count distinct `order_key` values.

3. Number of line records:
   Count MongoDB documents.

4. Procurement spending/value:
   Sum the `total_price` field.

5. Average order value:
   First group documents by `order_key` and sum
   `total_price`, then calculate the average of those
   order totals.

6. Primary time field:
   `creation_date`.

7. Time helper fields:
   - year
   - month
   - quarter
   - fiscal_year

Important fields:

- order_key
- purchase_order_number
- requisition_number

- creation_date
- purchase_date
- fiscal_year
- year
- month
- quarter

- department_name

- supplier_code
- supplier_name
- supplier_qualifications
- supplier_zip_code

- acquisition_type
- sub_acquisition_type
- acquisition_method
- sub_acquisition_method

- lpa_number
- calcard

- item_name
- item_description

- quantity
- unit_price
- total_price

- classification_codes
- normalized_unspsc
- commodity_title
- class
- class_title
- family
- family_title
- segment

Important interpretation rules:

- supplier_code should be preferred when identifying
  a supplier because it is normalized.
- supplier_name should normally be used for display.
- department_name is the normalized purchasing department.
- total_price represents procurement value at line level.
- quantity and line frequency are different concepts.
- "most frequently ordered item" normally means number
  of line occurrences unless the user explicitly asks
  for total quantity.
"""


ALLOWED_FIELDS = {
    "order_key",
    "purchase_order_number",
    "requisition_number",

    "creation_date",
    "purchase_date",
    "fiscal_year",
    "year",
    "month",
    "quarter",

    "department_name",

    "supplier_code",
    "supplier_name",
    "supplier_qualifications",
    "supplier_zip_code",

    "acquisition_type",
    "sub_acquisition_type",
    "acquisition_method",
    "sub_acquisition_method",

    "lpa_number",
    "calcard",

    "item_name",
    "item_description",

    "quantity",
    "unit_price",
    "total_price",

    "classification_codes",
    "normalized_unspsc",
    "commodity_title",
    "class",
    "class_title",
    "family",
    "family_title",
    "segment",
}