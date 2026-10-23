SELECT
    t.transaction_id,
    t.account_number,
    t.transaction_date,
    t.transaction_amount,
    t.transaction_type,
    t.transaction_narrative,
    t.transaction_code,
    t.transaction_code_desc,
    t.counterparty_bsb,
    t.counterparty_name,
    t.counterparty_country
FROM transaction_data t
INNER JOIN account_data a ON t.account_number = a.account_number
WHERE a.party_id = :party_id
  AND (:from_date IS NULL OR t.transaction_date >= :from_date)
  AND (:to_date   IS NULL OR t.transaction_date <= :to_date)
ORDER BY t.transaction_date ASC;
