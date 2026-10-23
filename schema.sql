-- AML Case Summary Script — Database Schema
-- Written in Cloud Spanner DDL (production target).
-- Local development uses SQLite with equivalent types (see setup.py).
-- Illustrative schema only — not for production use as-is.

CREATE TABLE party_data (
    party_id            STRING(36)      NOT NULL,
    full_name           STRING(255),
    date_of_birth       DATE,
    address             STRING(500),
    nationality         STRING(100),
    entity_type         STRING(20)      NOT NULL,   -- INDIVIDUAL | ENTITY
    acn                 STRING(20),                 -- Australian Company Number (entities only)
    abn                 STRING(20),                 -- Australian Business Number (entities only)
    risk_rating         STRING(10)      NOT NULL,   -- LOW | MEDIUM | HIGH
    pep_flag            STRING(1)       NOT NULL,   -- Y | N
    sanctions_flag      STRING(1)       NOT NULL,   -- Y | N
) PRIMARY KEY (party_id);


CREATE TABLE account_data (
    account_id          STRING(36)      NOT NULL,
    party_id            STRING(36)      NOT NULL,
    account_type        STRING(20)      NOT NULL,   -- SAVINGS | TRANSACTION | BUSINESS
    account_number      STRING(50)      NOT NULL,
    account_status      STRING(20)      NOT NULL,   -- ACTIVE | DORMANT | CLOSED
    open_date           DATE            NOT NULL,
    close_date          DATE,                       -- NULL if account is still open
) PRIMARY KEY (account_id);


CREATE TABLE transaction_data (
    transaction_id          STRING(36)      NOT NULL,
    account_number          STRING(50)      NOT NULL,
    transaction_date        DATE            NOT NULL,
    transaction_amount      FLOAT64         NOT NULL,
    transaction_type        STRING(10)      NOT NULL,   -- CREDIT | DEBIT
    transaction_narrative   STRING(500),
    transaction_code        STRING(10)      NOT NULL,   -- e.g. 001 | 002 | 003
    transaction_code_desc   STRING(100)     NOT NULL,   -- e.g. Purchase | Cash Withdrawal | Cash Deposit
    counterparty_bsb        STRING(10),
    counterparty_name       STRING(255),
    counterparty_country    STRING(100),
) PRIMARY KEY (transaction_id);


CREATE TABLE alert_data (
    alert_id            STRING(36)      NOT NULL,
    party_id            STRING(36)      NOT NULL,
    alert_type          STRING(50)      NOT NULL,   -- STRUCTURING | HIGH_VOLUME | PEP_MATCH | SANCTIONS_HIT
    alert_date          DATE            NOT NULL,
    alert_status        STRING(20)      NOT NULL,   -- OPEN | CLOSED | ESCALATED
    alert_source        STRING(100)     NOT NULL,
    description         STRING(1000),
) PRIMARY KEY (alert_id);
