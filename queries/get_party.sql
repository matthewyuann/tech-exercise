SELECT
    party_id,
    full_name,
    date_of_birth,
    address,
    nationality,
    entity_type,
    acn,
    abn,
    risk_rating,
    pep_flag,
    sanctions_flag
FROM party_data
WHERE party_id = :party_id;
