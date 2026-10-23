SELECT
    alert_id,
    party_id,
    alert_type,
    alert_date,
    alert_status,
    alert_source,
    description
FROM alert_data
WHERE party_id = :party_id
ORDER BY alert_date DESC;
