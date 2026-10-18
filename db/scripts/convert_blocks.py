"""Convert GeoLite2 *-Blocks-*.csv (CIDR) to the hex-range format used by the
MaxMind MySQL import guide (replaces the closed-source geoip2-csv-converter).

usage: convert_blocks.py <in.csv> <out.csv>
Output columns: network_start_hex, network_end_hex, <remaining input columns...>
"""
import csv
import ipaddress
import sys


def main(src: str, dst: str) -> None:
    with open(src, newline="", encoding="utf-8") as fin, \
            open(dst, "w", newline="", encoding="utf-8") as fout:
        reader = csv.reader(fin)
        writer = csv.writer(fout, lineterminator="\n")
        header = next(reader)
        writer.writerow(["network_start", "network_end"] + header[1:])
        for row in reader:
            net = ipaddress.ip_network(row[0])
            writer.writerow([net.network_address.packed.hex(),
                             net.broadcast_address.packed.hex()] + row[1:])


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])
