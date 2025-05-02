DROP TABLE IF EXISTS transactions;
DROP TABLE IF EXISTS wallets;
DROP TABLE IF EXISTS currencies;
DROP TABLE IF EXISTS locations;
DROP TABLE IF EXISTS device_types;

CREATE TABLE IF NOT EXISTS wallets (
    wallet_id VARCHAR(250) PRIMARY KEY,
    wallet_address TEXT UNIQUE NOT NULL
);

CREATE TABLE IF NOT EXISTS currencies (
    currency_id SMALLSERIAL PRIMARY KEY,
    currency_code VARCHAR(10) UNIQUE NOT NULL
);

CREATE TABLE IF NOT EXISTS locations (
    location_id SMALLSERIAL PRIMARY KEY,
    country_name TEXT UNIQUE NOT NULL
);

CREATE TABLE IF NOT EXISTS device_types (
    device_type_id SMALLSERIAL PRIMARY KEY,
    device_name TEXT UNIQUE NOT NULL
);

CREATE TABLE IF NOT EXISTS transactions (
    transaction_id UUID PRIMARY KEY,
    timestamp TIMESTAMP NOT NULL,
    sender_wallet_id VARCHAR(250) NOT NULL,
    receiver_wallet_id VARCHAR(250) NOT NULL,
    amount NUMERIC(18, 6) NOT NULL,
    currency_id SMALLINT NOT NULL,
    gas_fee NUMERIC(18, 6) NOT NULL,
    is_smart_contract BOOLEAN NOT NULL,
    location_id SMALLINT,
    device_type_id SMALLINT,
    is_fraud BOOLEAN,

    CONSTRAINT fk_currency FOREIGN KEY (currency_id) REFERENCES currencies(currency_id),
    CONSTRAINT fk_location FOREIGN KEY (location_id) REFERENCES locations(location_id),
    CONSTRAINT fk_device_type FOREIGN KEY (device_type_id) REFERENCES device_types(device_type_id)
);

CREATE INDEX IF NOT EXISTS idx_currency_id ON transactions(currency_id);
CREATE INDEX IF NOT EXISTS idx_location_id ON transactions(location_id);
CREATE INDEX IF NOT EXISTS idx_device_type_id ON transactions(device_type_id);
CREATE INDEX IF NOT EXISTS idx_is_fraud ON transactions(is_fraud);
CREATE INDEX IF NOT EXISTS idx_timestamp ON transactions(timestamp);
CREATE INDEX IF NOT EXISTS idx_sender_receiver ON transactions(sender_wallet_id, receiver_wallet_id);

INSERT INTO currencies (currency_code) VALUES ('BTC'),('ETH'),('PI');

INSERT INTO locations (country_name) VALUES ('United States'),('Canada'),('Germany'),('Nigeria'),('Ghana');

INSERT INTO device_types (device_name) VALUES ('mobile'),('desktop'),('API');
