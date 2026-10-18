-- Country for an IP (v4 or v6). Falls back to the registered country when the
-- block has no geoname_id (e.g. anycast / unlocated ranges).
-- Set the address first, e.g.: SET @ip = '83.149.9.216';
SELECT loc.country_iso_code, loc.country_name
FROM (
  SELECT * FROM geoip2_network
  WHERE LENGTH(INET6_ATON(@ip)) = LENGTH(network_start)
    AND INET6_ATON(@ip) >= network_start
  ORDER BY network_start DESC
  LIMIT 1
) net
LEFT JOIN geoip2_location loc
  ON loc.geoname_id = COALESCE(net.geoname_id, net.registered_country_geoname_id)
 AND loc.locale_code = 'en'
WHERE INET6_ATON(@ip) <= net.network_end;
