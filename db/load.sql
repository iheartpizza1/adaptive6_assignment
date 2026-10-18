-- Run with: mysql --local-infile=1 -u root -p geoip < load.sql   (from the db/ directory)
SET GLOBAL local_infile = 1;

LOAD DATA LOCAL INFILE 'generated/GeoLite2-Country-Blocks-IPv4-Hex.csv'
INTO TABLE geoip2_network
FIELDS TERMINATED BY ',' ENCLOSED BY '"' LINES TERMINATED BY '\n' IGNORE 1 ROWS
(@network_start, @network_end, @geoname_id, @registered_country_geoname_id,
 @represented_country_geoname_id, @is_anonymous_proxy, @is_satellite_provider, @is_anycast)
SET network_start = UNHEX(@network_start),
    network_end = UNHEX(@network_end),
    geoname_id = NULLIF(@geoname_id, ''),
    registered_country_geoname_id = NULLIF(@registered_country_geoname_id, ''),
    represented_country_geoname_id = NULLIF(@represented_country_geoname_id, ''),
    is_anonymous_proxy = NULLIF(@is_anonymous_proxy, ''),
    is_satellite_provider = NULLIF(@is_satellite_provider, ''),
    is_anycast = NULLIF(@is_anycast, '');

LOAD DATA LOCAL INFILE 'generated/GeoLite2-Country-Blocks-IPv6-Hex.csv'
INTO TABLE geoip2_network
FIELDS TERMINATED BY ',' ENCLOSED BY '"' LINES TERMINATED BY '\n' IGNORE 1 ROWS
(@network_start, @network_end, @geoname_id, @registered_country_geoname_id,
 @represented_country_geoname_id, @is_anonymous_proxy, @is_satellite_provider, @is_anycast)
SET network_start = UNHEX(@network_start),
    network_end = UNHEX(@network_end),
    geoname_id = NULLIF(@geoname_id, ''),
    registered_country_geoname_id = NULLIF(@registered_country_geoname_id, ''),
    represented_country_geoname_id = NULLIF(@represented_country_geoname_id, ''),
    is_anonymous_proxy = NULLIF(@is_anonymous_proxy, ''),
    is_satellite_provider = NULLIF(@is_satellite_provider, ''),
    is_anycast = NULLIF(@is_anycast, '');

LOAD DATA LOCAL INFILE 'generated/GeoLite2-Country-Locations-en.csv'
INTO TABLE geoip2_location
FIELDS TERMINATED BY ',' ENCLOSED BY '"' LINES TERMINATED BY '\n' IGNORE 1 ROWS
(geoname_id, locale_code, @continent_code, @continent_name,
 @country_iso_code, @country_name, @is_in_european_union)
SET continent_code = NULLIF(@continent_code, ''),
    continent_name = NULLIF(@continent_name, ''),
    country_iso_code = NULLIF(@country_iso_code, ''),
    country_name = NULLIF(@country_name, ''),
    is_in_european_union = NULLIF(@is_in_european_union, '');
