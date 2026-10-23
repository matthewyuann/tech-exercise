SELECT
    account_id,
    party_id,
    account_type,
    account_number,
    account_status,
    open_date,
    close_date
FROM account_data
WHERE party_id = :party_id
ORDER BY open_date ASC;
