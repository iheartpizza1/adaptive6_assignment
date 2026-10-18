-- GeoLite2 *Country* schema, adapted from
-- https://dev.maxmind.com/geoip/importing-databases/mysql/ (the guide shows the City edition;
-- the Country CSVs have fewer columns).
CREATE DATABASE IF NOT EXISTS geoip CHARACTER SET utf8mb4;
USE geoip;

DROP TABLE IF EXISTS geoip2_network;
CREATE TABLE geoip2_network (
  network_start varbinary(16) NOT NULL,
  network_end varbinary(16) NOT NULL,
  geoname_id int,
  registered_country_geoname_id int,
  represented_country_geoname_id int,
  is_anonymous_proxy bool,
  is_satellite_provider bool,
  is_anycast bool,
  INDEX (network_start),
  INDEX (network_end)
);

DROP TABLE IF EXISTS geoip2_location;
CREATE TABLE geoip2_location (
  geoname_id int NOT NULL,
  locale_code varchar(8) NOT NULL,
  continent_code varchar(4),
  continent_name varchar(64),
  country_iso_code varchar(4),
  country_name varchar(128),
  is_in_european_union bool,
  PRIMARY KEY (geoname_id, locale_code)
);
